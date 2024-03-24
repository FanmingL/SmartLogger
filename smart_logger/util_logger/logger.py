import atexit
import os
import shutil
import time
from datetime import datetime

import numpy as np

from smart_logger.common import common_config
from smart_logger.common.common_config import system
from smart_logger.util_logger.logger_base import LoggerBase


class Logger(LoggerBase):
    logger = None

    def __init__(self, log_to_file=True, log_name='log', force_backup=False,
                 log_signature=None, logger_category=None, base_path=None, backup_code=True):
        # 初始化函数，可传入以下参数：
        # log_to_file: 是否将日志记录到文件中，默认为True。
        # log_name: 日志文件名，默认为'log'。
        # force_backup: 是否强制备份日志文件，默认为False。
        # log_signature: 在日志开始处添加一个签名行，默认为None。
        # logger_category: 日志分类，在log文件夹下创建不同的子文件夹存放分类日志，默认为None。
        # base_path: 日志文件夹所在的基础路径，默认为None，表示使用config.py中的默认路径。
        self.log_name = log_name
        self.logger_category = logger_category
        # 获取日志文件夹路径
        base_path = base_path if base_path is not None else common_config.get_log_base_path()
        if self.logger_category is not None:
            self.output_dir = os.path.join(base_path, common_config.LOG_FOLDER_NAME, self.logger_category, log_name)
        else:
            self.output_dir = os.path.join(base_path, common_config.LOG_FOLDER_NAME, log_name)
        # 创建日志文件夹
        os.makedirs(self.output_dir, exist_ok=True)
        # 备份日志文件
        bk_log_file = False
        if log_to_file:
            if os.path.exists(os.path.join(self.output_dir, 'log.txt')):
                shutil.move(os.path.join(self.output_dir, "log.txt"), os.path.join(self.output_dir, "log_back.txt"))
                bk_log_file = True
            self.log_file = open(os.path.join(self.output_dir, 'log.txt'), 'w')
            atexit.register(self.log_file.close)
        else:
            self.log_file = None
        # 调用父类Logger的初始化函数
        super(Logger, self).__init__(self.output_dir, log_file=self.log_file)
        self.current_data = {}
        self.logged_data = set()
        # 备份日志文件
        self.make_log_backup(log_signature, force_backup, has_bk_logtxt=bk_log_file)
        # 初始化csv文件
        self.init_csv()
        # 初始化tensorboard
        self.init_tb()
        # 备份代码文件
        if backup_code:
            self.backup_code()
        # 备份环境当前环境
        self.save_env()
        self.tb_header_dict = {}
        # 如果当前没有默认Logger，则将自己设为默认Logger
        if Logger.logger is None:
            self.set_as_default_logger()

    @staticmethod
    def init_global_logger(log_to_file=True, log_name='log', force_backup=False,
                           log_signature=None, logger_category=None, base_path=None, backup_code=True):
        Logger.logger = Logger(log_to_file=log_to_file, log_name=log_name, force_backup=force_backup,
                               log_signature=log_signature, logger_category=logger_category, base_path=base_path,
                               backup_code=backup_code)

    def set_as_default_logger(self):
        Logger.logger = self

    @staticmethod
    def local_log(*args, **kwargs):
        if Logger.logger is not None:
            Logger.logger.logger(*args, **kwargs)
        else:
            print(*args, **kwargs)

    @staticmethod
    def add_key_suffix(suffix, data: dict):
        result = dict()
        for k, v in data.items():
            result[k + suffix] = v
        return result

    def make_log_backup(self, log_signature, force_backup, has_bk_logtxt):
        # 如果输出目录不存在，先创建
        if not os.path.exists(self.output_dir):
            self.log(f'directory {self.output_dir} does not exist, create it...')
        else:
            # signature.txt 存在于输出目录中
            signature_file = os.path.join(self.output_dir, 'signature.txt')
            # 如果 log_signature 为 None 并且不需要强制备份
            if log_signature is None and not force_backup:
                # 记录日志：log_signature 为空，文件将会被覆盖
                self.log(f'log_signature is None, file will be overwriten anyway...')
            # 如果 signature.txt 不存在
            elif not os.path.exists(signature_file):
                # 记录日志：signature 文件不存在，文件将会被覆盖
                self.log(f'signature file does not exist, file will be overwriten anyway...')
                with open(signature_file, 'w') as f:
                    f.write(log_signature)  # 将 log_signature 写入 signature.txt
            else:
                # 记录日志：输出目录存在，正在检查文件完整性
                self.log(f'directory {self.output_dir} exists, checking identity...')
                sig = None
                try:
                    with open(signature_file, 'r') as f:
                        sig = f.read()
                except Exception as e:
                    # 记录日志：读取 signature_file 错误
                    self.log(f'{signature_file} read fail!!!')
                # 如果 log_signature 不为空，sig 等于 log_signature 并且不需要强制备份
                if log_signature is not None and sig == log_signature and not force_backup:
                    # 记录日志：配置完全相同，文件将会被覆盖
                    self.log(f'config is completely same, file will be overwrited anyway...')
                else:
                    # 记录日志：配置不相同，开始备份文件
                    self.log(f'config is not same, file will backup first...')
                    # 备份目录为当前时间命名
                    backup_dir = os.path.join(common_config.get_base_path(), common_config.LOG_FOLDER_NAME_BK,
                                              f"backup_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
                    os.makedirs(backup_dir, exist_ok=True)  # 创建备份目录
                    # 复制文件到备份目录中，并记录进度日志
                    shutil.copytree(self.output_dir, os.path.join(backup_dir, os.path.basename(self.output_dir)), dirs_exist_ok=True)
                    if has_bk_logtxt:
                        # 获取日志文件路径
                        logbk_file = os.path.join(backup_dir, os.path.basename(self.output_dir), 'log_back.txt')
                        lognew_file = os.path.join(backup_dir, os.path.basename(self.output_dir), 'log.txt')
                        if os.path.exists(logbk_file):
                            # 将旧的日志文件重命名为 log.txt，并记录日志
                            # system(f'mv \"{logbk_file}\" \"{lognew_file}\"', lambda x: self.log(x))
                            shutil.move(logbk_file, lognew_file)
                    if log_signature is not None:
                        with open(signature_file, 'w') as f:
                            f.write(log_signature)  # 写入新的 signature.txt

    def backup_code(self):
        # 获取基础路径
        base_path = common_config.get_base_path()
        # 存储需要备份的文件列表
        things = []

        # 判断文件是否需要被备份
        def need_backup(name: str):
            # 遍历忽略的头部，如果文件名以指定的头部开始，则不需要备份
            for ignore_head in common_config.BACKUP_IGNORE_HEAD:
                if name.startswith(ignore_head):
                    return False
            # 遍历忽略的关键词，如果文件名包含指定的关键词，则不需要备份
            for ignore_key in common_config.BACKUP_IGNORE_KEY:
                if ignore_key in name:
                    return False
            # 遍历忽略的尾部，如果文件名以指定的尾部结束，则不需要备份
            for ignore_tail in common_config.BACKUP_IGNORE_TAIL:
                if name.endswith(ignore_tail):
                    return False
            # 如果文件名不包含上述要忽略的内容，则需要备份该文件
            return True

        # 遍历基础路径下的文件夹和文件，如果需要备份则将其加入到things列表中
        for item in os.listdir(base_path):
            p = os.path.join(base_path, item)
            if need_backup(item):
                things.append(p)

        # 将备份的代码存储在codes目录下，如果不存在则创建该目录
        code_path = os.path.join(self.output_dir, 'codes')
        os.makedirs(code_path, exist_ok=True)

        # 遍历需要备份的文件列表进行备份，采用rsync命令备份，如果不存在则使用cp备份
        for item in things:
            if os.system('which rsync > /dev/null'):
                # 检查源路径是文件还是目录
                if os.path.isfile(item):
                    # 如果是文件，就用shutil.copy2()
                    shutil.copy2(item, code_path)
                elif os.path.isdir(item):
                    # 如果是目录，就用shutil.copytree()
                    # 注意：目标路径必须不存在，所以在目标路径下创建一个与源目录同名的新目录
                    shutil.copytree(item, os.path.join(code_path, os.path.basename(item)))
            else:
                ignore_str = ''
                # 构造rsync命令中的忽略选项，逐个添加到ignore_str中
                for ignore_head in common_config.BACKUP_IGNORE_HEAD:
                    ignore_str += f' --exclude \"{ignore_head}*\" '
                for ignore_key in common_config.BACKUP_IGNORE_KEY:
                    ignore_str += f' --exclude \"*{ignore_key}*\" '
                for ignore_tail in common_config.BACKUP_IGNORE_TAIL:
                    ignore_str += f' --exclude \"*{ignore_tail}\" '

                # 执行rsync命令进行文件备份，备份失败则使用cp命令进行备份
                if system(f'rsync -razm {ignore_str} \"{item}\" \"{code_path}\"',
                          lambda x: self.log(f'[Code Backingup] {x}')):
                    self.log(f'error occurs when rsync, use cp instead!')
                    # 检查源路径是文件还是目录
                    if os.path.isfile(item):
                        # 如果是文件，就用shutil.copy2()
                        shutil.copy2(item, code_path)
                    elif os.path.isdir(item):
                        # 如果是目录，就用shutil.copytree()
                        # 注意：目标路径必须不存在，所以在目标路径下创建一个与源目录同名的新目录
                        shutil.copytree(item, os.path.join(code_path, os.path.basename(item)))

        # 使用tar命令将备份的代码打包成tar文件，如果异常则使用zip进行打包
        try:
            if os.path.exists(code_path + '.tar'):
                os.remove(code_path + ".tar")
            archive_data = shutil.make_archive(code_path, 'tar', base_dir='codes', root_dir=os.path.dirname(code_path))
            self.log(f'archive codes done! file is saved to {archive_data}')
        except Exception as e:
            self.log(f'fail to make archive file with tar command because of {e}, try to use zip instead.')
            if os.path.exists(os.path.join(self.output_dir, "codes.zip")):
                os.remove(os.path.join(self.output_dir, "codes.zip"))
            system(f'cd {self.output_dir} &&  zip -r codes.zip codes', lambda x: self.log(x))
        finally:
            # 删除备份的代码目录
            shutil.rmtree(code_path, ignore_errors=True)

    def sync_log_to_remote(self, replace=False, trial_num=1):
        import paramiko
        # 重试多次
        for _ in range(trial_num):
            # 遍历指定的机器IP
            for target_machine_ind in range(len(common_config.MAIN_MACHINE_IP)):
                # 从配置文件获取主机IP、端口、用户名、密码及日志路径
                _ip, _port = map(lambda x: x[target_machine_ind], [
                    common_config.MAIN_MACHINE_IP, common_config.MAIN_MACHINE_PORT,
                ])
                _user, _passwd, _log_path = common_config.MAIN_MACHINE_USER, \
                    common_config.MAIN_MACHINE_PASSWD, \
                    common_config.MAIN_MACHINE_LOG_PATH
                # 删除末尾的斜杠
                while _log_path.endswith('/'):
                    _log_path = _log_path[:-1]
                while self.output_dir.endswith('/'):
                    self.output_dir = self.output_dir[:-1]
                try:
                    ssh = paramiko.SSHClient()
                    # 如果主机没有记录在known_hosts中，自动添加
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    # 连接主机
                    ssh.connect(hostname=_ip, port=_port, username=_user,
                                password=_passwd, timeout=5)
                    # 创建远程日志目录
                    self.log(f'ssh {_user}@{_ip} "mkdir -p {_log_path}"')
                    _, stdout, _ = ssh.exec_command(f'mkdir -p {_log_path}')

                    local_path = self.output_dir
                    if self.logger_category is None:
                        # 如果logger_category为空，则直接使用log_name作为远程日志文件名
                        remote_path = os.path.join(_log_path, self.log_name)
                    else:
                        # 否则，将log_name放在logger_category目录下
                        remote_path = os.path.join(_log_path, self.logger_category, self.log_name)

                    process_dir = set()
                    # 遍历本地日志目录
                    for root, _, files in os.walk(local_path, topdown=True, followlinks=True):
                        for file in files:
                            full_path_in_local = os.path.join(root, file)
                            full_path_in_remote = full_path_in_local.replace(local_path, remote_path)
                            full_path_remote_dir = os.path.dirname(full_path_in_remote)
                            # 如果目录没有被处理过，则尝试创建或删除再创建
                            if full_path_remote_dir not in process_dir:
                                full_path_remote_dir_normal = full_path_remote_dir.replace(' ', '\ ')
                                full_path_remote_dir_normal = full_path_remote_dir_normal.replace('&', '\&')
                                if replace:
                                    rm_cmd = f'rm -rf {full_path_remote_dir_normal} && mkdir -p {full_path_remote_dir_normal}'
                                    _, stdout, _ = ssh.exec_command(rm_cmd)
                                    self.log(f"ssh {_user}@{_ip} {rm_cmd}")
                                else:
                                    mkdir_cmd = f'mkdir -p {full_path_remote_dir_normal}'
                                    _, stdout, _ = ssh.exec_command(mkdir_cmd)
                                    self.log(mkdir_cmd)
                                process_dir.add(full_path_remote_dir)

                    t = paramiko.Transport((_ip, _port))
                    t.connect(username=_user, password=_passwd)
                    sftp = paramiko.SFTPClient.from_transport(t)
                    # 再次遍历本地日志目录，将文件复制到远端主机
                    for root, _, files in os.walk(local_path, topdown=False, followlinks=True):
                        for file in files:
                            full_path_in_local = os.path.join(root, file)
                            full_path_in_remote = full_path_in_local.replace(local_path, remote_path)
                            self.log(f'sync local: {full_path_in_local} to '
                                     f'{_user}@{_ip}:{full_path_in_remote}')
                            full_path_in_remote_no_process = full_path_in_remote
                            full_path_in_remote = full_path_in_remote.replace(' ', '\ ')
                            full_path_in_remote = full_path_in_remote.replace('&', '\&')

                            for _ in range(10):
                                try:
                                    sftp.put(full_path_in_local, full_path_in_remote_no_process, confirm=False)
                                    break
                                except FileNotFoundError as e:
                                    # 如果远端目录不存在，则创建
                                    full_path_remote_dir = os.path.dirname(full_path_in_remote)
                                    self.log(f'file {full_path_remote_dir} not found!!')
                                    mkdir_cmd = f'mkdir -p {full_path_remote_dir}'
                                    _, stdout, _ = ssh.exec_command(mkdir_cmd)
                                    self.log(mkdir_cmd)
                    t.close()
                    ssh.close()
                    self.log(f'transfer the log to {_user}@{_ip}:{_log_path} success!!!')
                    return True
                except Exception as e:
                    import traceback
                    self.log(traceback.print_exc())
                    self.log(f'Error occur while transferring the log to {_ip}, {e}')
                    continue
        return False

    def debug(self, info):
        self.log(f"[ DEBUG ]: {info}")  # 输出DEBUG级别的日志信息

    def info(self, info):
        self.log(f"[ INFO ]: {info}")  # 输出INFO级别的日志信息

    def error(self, info):
        self.log(f"[ ERROR ]: {info}")  # 输出ERROR级别的日志信息

    def log(self, *args, color=None, bold=True):
        super(Logger, self).log(*args, color=color, bold=bold)  # 记录并输出日志信息（可设置字体颜色和加粗）

    def log_dict(self, color=None, bold=False, **kwargs):
        for k, v in kwargs.items():
            super(Logger, self).log('{}: {}'.format(k, v), color=color, bold=bold)  # 记录和输出字典类型的日志信息

    def log_dict_single(self, data, color=None, bold=False):
        for k, v in data.items():
            super(Logger, self).log('{}: {}'.format(k, v), color=color, bold=bold)  # 记录和输出单个字典类型的日志信息

    def __call__(self, *args, **kwargs):
        self.log(*args, **kwargs)

    def log_tabular(self, key, val=None, tb_prefix=None, with_min_and_max=False, average_only=False, no_tb=False):
        # 如果有val，记录键值对
        if val is not None:
            super(Logger, self).log_tabular(key, val, tb_prefix, no_tb=no_tb)
        else:
            # 记录当前数据的平均值，加入到已记录数据的集合中
            if key in self.current_data:
                self.logged_data.add(key)
                super(Logger, self).log_tabular(key if average_only else "Average" + key,
                                                np.mean(self.current_data[key]), tb_prefix, no_tb=no_tb)
                # 如果不是仅记录平均值，则记录标准差和最大最小值
                if not average_only:
                    super(Logger, self).log_tabular("Std" + key,
                                                    np.std(self.current_data[key]), tb_prefix, no_tb=no_tb)
                    if with_min_and_max:
                        super(Logger, self).log_tabular("Min" + key, np.min(self.current_data[key]), tb_prefix,
                                                        no_tb=no_tb)
                        super(Logger, self).log_tabular('Max' + key, np.max(self.current_data[key]), tb_prefix,
                                                        no_tb=no_tb)

    def add_tabular_data(self, tb_prefix=None, **kwargs):
        for k, v in kwargs.items():
            if tb_prefix is not None and k not in self.tb_header_dict:
                self.tb_header_dict[k] = tb_prefix
            if k not in self.current_data:
                self.current_data[k] = []
            if not isinstance(v, list):
                self.current_data[k].append(v)
            else:
                self.current_data[k] += v

    def update_tb_header_dict(self, tb_header_dict):
        self.tb_header_dict.update(tb_header_dict)

    def dump_tabular(self):
        for k in self.current_data:
            if k not in self.logged_data:
                if k in self.tb_header_dict:
                    self.log_tabular(k, tb_prefix=self.tb_header_dict[k], average_only=True)
                else:
                    self.log_tabular(k, average_only=True)
        self.logged_data.clear()
        self.current_data.clear()
        super(Logger, self).dump_tabular()


if __name__ == '__main__':
    logger = Logger(log_name='log2', force_backup=True)
    logger.log(122, '22', color='red', bold=False)
    data = {'a': 10, 'b': 11, 'c': 13}
    for i in range(100):
        for _ in range(10):
            for k in data:
                data[k] += 1
            logger.add_tabular_data(**data)
        # logger.sync_log_to_remote()
        logger.log_tabular('a')
        logger.dump_tabular()
        time.sleep(1)
