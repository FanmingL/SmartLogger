try:
    from torch.utils.tensorboard import SummaryWriter
except Exception as e:
    from tensorboardX import SummaryWriter
import time, atexit, copy
import os
import os.path as osp
from smart_logger.common import common_config
from smart_logger.common.common_config import system
color2num = dict(
    gray=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
    magenta=35,
    cyan=36,
    white=37,
    crimson=38
)


def colorize(string, color, bold=False, highlight=False):
    """
    Colorize a string.

    This function was originally written by John Schulman.
    """
    if color is None:
        return string
    attr = []
    num = color2num[color]
    if highlight: num += 10
    attr.append(str(num))
    if bold: attr.append('1')

    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)


class LoggerBase:
    def __init__(self, output_dir=None, output_fname='progress.csv', exp_name=None, log_file=None):
        self.output_dir = output_dir or "/tmp/experiments/%i" % int(time.time())
        self.output_tb_dir = os.path.join(self.output_dir, 'tbfile')
        self.base_log_file = log_file
        self.tb = None
        os.makedirs(self.output_dir, exist_ok=True)
        output_file_name = osp.join(self.output_dir, output_fname)
        self.output_fname = output_fname
        self.output_file = open(output_file_name, 'w')
        atexit.register(self.output_file.close)
        self.log("Logging data to %s" % self.output_file.name, color='green')
        self.first_row = True
        self.log_headers = []
        self.log_headers_set = set()
        self.log_current_row = {}
        self.log_last_row = None
        self.exp_name = exp_name
        self.spliter = ','
        self.tb_x_label = None
        self.tb_x = None
        self.first_row_changed = False
        self.step = 0

    def init_tb(self):
        if osp.exists(self.output_tb_dir):
            self.log("Warning: Log dir %s already exists! Storing info there anyway." % self.output_dir, color='blue')
            cmd = f'rm -rf {self.output_tb_dir}'
            system(cmd, lambda x: self.log(x))
        os.makedirs(self.output_tb_dir)
        self.tb = SummaryWriter(self.output_tb_dir)

    def set_tb_x_label(self, label):
        self.tb_x_label = label

    def register_keys(self, keys):
        """
        this keys will may not be added to tabular data at the first step, thus,
        they should be manually logged at the first step.
        :param keys:
        :return:
        """
        for key in keys:
            self.log_tabular(key, 0, no_tb=True)

    def set_log_file(self, log_file):
        self.base_log_file = log_file

    def log(self, *args, color=None, bold=True):
        s = ''
        for item in args[:-1]:
            s += str(item) + ' '
        s += str(args[-1])
        print(colorize(s, color, bold=bold))
        if self.base_log_file is not None:
            print(s, file=self.base_log_file)
            self.base_log_file.flush()

    def log_tabular(self, key, val, tb_prefix=None, no_tb=False):
        if self.tb_x_label is not None and key == self.tb_x_label:
            self.tb_x = val
        if self.first_row:
            self.log_headers.append(key)
            self.log_headers_set.add(key)
            self.log_headers = sorted(self.log_headers)
        else:
            if key not in self.log_headers_set:
                self.log_headers.append(key)
                self.log_headers_set.add(key)
                self.first_row_changed = True
        assert key not in self.log_current_row, f"You already set {key} this " \
                                                f"iteration. Maybe you forgot to call dump_tabular()"
        self.log_current_row[key] = val
        if tb_prefix is None:
            tb_prefix = 'tb'
        if not no_tb:
            if self.tb_x_label is None:
                self.tb.add_scalar(f'{tb_prefix}/{key}', val, self.step)
            else:
                self.tb.add_scalar(f'{tb_prefix}/{key}', val, self.tb_x)

    def dump_tabular(self):
        if self.first_row:
            self.log_last_row = self.log_current_row
        for k, v in self.log_last_row.items():
            if k not in self.log_current_row:
                self.log_current_row[k] = v
        vals = []
        key_lens = [len(key) for key in self.log_headers]
        if len(key_lens) > 0:
            max_key_len = max(15, max(key_lens))
        else:
            max_key_len = 15
        keystr = '%' + '%d' % max_key_len
        fmt = "| " + keystr + "s | %15s |"
        n_slashes = 22 + max_key_len

        head_indication = f" iter {self.step} "
        # print("-" * n_slashes)
        bar_num = n_slashes - len(head_indication)
        self.log("-" * (bar_num // 2) + head_indication + "-" * (bar_num // 2))
        for key in self.log_headers:
            val = self.log_current_row.get(key, "")
            valstr = "%8.3g" % val if hasattr(val, "__float__") else val
            self.log(fmt % (key, valstr))
            vals.append(val)
        self.log("-" * n_slashes+'\n')
        if self.output_file is not None:
            if self.first_row:
                self.output_file.write(self.spliter.join(self.log_headers) + "\n")
            if self.first_row_changed:
                self.first_row_changed = False
                self.rewrite_file()

            self.output_file.write(self.spliter.join(map(str, vals)) + "\n")
            self.output_file.flush()
        self.log_last_row = copy.deepcopy(self.log_current_row)
        self.log_current_row.clear()
        self.first_row = False
        self.step += 1

    def rewrite_file(self):
        self.output_file.close()
        old_output_file = os.path.join(self.output_dir, self.output_fname)
        bk_output_file = os.path.join(self.output_dir, self.output_fname+'back')
        with open(old_output_file, 'r') as f:
            with open(bk_output_file, 'w') as f_out:
                f_out.write(self.spliter.join(self.log_headers) + "\n")
                first_line = f.readline()
                additional_num = len(self.log_headers) - len(first_line.split(self.spliter))
                additional_header = self.log_headers[-additional_num:]
                for line in f:
                    vals = line[:-1].split(self.spliter) + ['0'] * additional_num
                    f_out.write(self.spliter.join(map(str, vals)) + "\n")
        system(f"mv {bk_output_file} {old_output_file}", lambda x: self.log(x))
        self.output_file = open(old_output_file, 'a')
        atexit.register(self.output_file.close)
        self.log(f"re-writen the csv file because of the additional header keys: {additional_header}")


if __name__ == '__main__':
    logger = LoggerBase(output_dir=os.path.join(common_config.get_base_path(), 'log_file', 'log_file', 'log_file'))
    logger.init_tb()
    logger.log('123123', '2232', color="green")
    for i in range(10):
        logger.log_tabular('a', i)
        logger.log_tabular('b', i)
        if i >= 3:
            logger.log_tabular('c', i)
        if i >= 7:
            logger.log_tabular('d', i)
        logger.dump_tabular()