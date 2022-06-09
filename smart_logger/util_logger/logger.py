from smart_logger.util_logger.logger_base import LoggerBase
from smart_logger.common.common_config import *
from datetime import datetime
import os
import numpy as np
import time
import atexit
import shutil


class Logger(LoggerBase):
    logger = None
    def __init__(self, log_to_file=True, log_name='log', force_backup=False,
                 log_signature=None, logger_category=None, base_path=None):
        self.log_name = log_name
        self.logger_category = logger_category
        base_path = base_path if base_path is not None else get_log_base_path()
        if self.logger_category is not None:
            self.output_dir = os.path.join(base_path, LOG_FOLDER_NAME, self.logger_category, log_name)
        else:
            self.output_dir = os.path.join(base_path, LOG_FOLDER_NAME, log_name)
        os.makedirs(self.output_dir, exist_ok=True)
        if log_to_file:
            if os.path.exists(os.path.join(self.output_dir, 'log.txt')):
                system(f'mv {os.path.join(self.output_dir, "log.txt")} {os.path.join(self.output_dir, "log_back.txt")}')
            self.log_file = open(os.path.join(self.output_dir, 'log.txt'), 'w')
            atexit.register(self.log_file.close)
        else:
            self.log_file = None
        super(Logger, self).__init__(self.output_dir, log_file=self.log_file)
        self.current_data = {}
        self.logged_data = set()
        self.make_log_backup(log_signature, force_backup)
        self.init_tb()
        self.backup_code()
        self.tb_header_dict = {}

    @staticmethod
    def init_global_logger(log_to_file=True, log_name='log', force_backup=False,
                           log_signature=None, logger_category=None, base_path=None):
        Logger.logger = Logger(log_to_file=log_to_file, log_name=log_name, force_backup=force_backup,
                               log_signature=log_signature, logger_category=logger_category, base_path=base_path)

    @staticmethod
    def add_key_suffix(suffix, data:dict):
        result = dict()
        for k, v in data.items():
            result[k + suffix] = v
        return result

    def make_log_backup(self, log_signature, force_backup):
        if not os.path.exists(self.output_dir):
            self.log(f'directory {self.output_dir} does not exist, create it...')
        else:
            signature_file = os.path.join(self.output_dir, 'signature.txt')
            if log_signature is None:
                self.log(f'log_signature is None, file will be overwriten anyway...')
            elif not os.path.exists(signature_file):
                self.log(f'signature file does not exist, file will be overwriten anyway...')
                with open(signature_file, 'w') as f:
                    f.write(log_signature)
            else:
                self.log(f'directory {self.output_dir} exists, checking identity...')

                with open(signature_file, 'r') as f:
                    sig = f.read()
                if sig == log_signature and not force_backup:
                    self.log(f'config is completely same, file will be overwrited anyway...')
                else:
                    self.log(f'config is not same, file will backup first...')
                    backup_dir = os.path.join(get_base_path(), LOG_FOLDER_NAME_BK,
                                              f"backup_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
                    os.makedirs(backup_dir, exist_ok=True)
                    system(f"cp -r {self.output_dir} {backup_dir}", lambda x: self.log(x))
                    with open(signature_file, 'w') as f:
                        f.write(log_signature)

    def backup_code(self):
        base_path = get_base_path()
        things = []

        def need_backup(name: str):
            for ignore_head in BACKUP_IGNORE_HEAD:
                if name.startswith(ignore_head):
                    return False
            for ignore_key in BACKUP_IGNORE_KEY:
                if ignore_key in name:
                    return False
            for ignore_tail in BACKUP_IGNORE_TAIL:
                if name.endswith(ignore_tail):
                    return False
            return True
        for item in os.listdir(base_path):
            p = os.path.join(base_path, item)
            if need_backup(item):
                things.append(p)
        code_path = os.path.join(self.output_dir, 'codes')
        os.makedirs(code_path, exist_ok=True)
        for item in things:
            system(f'cp -r {item} {code_path}', lambda x: self.log(f'code backing up: {x}'))
        try:
            if os.path.exists(code_path + '.tar'):
                system(f'rm {code_path + ".tar"}', lambda x: self.log(x))
            archive_data = shutil.make_archive(code_path, 'tar', base_dir='codes', root_dir=os.path.dirname(code_path))
            self.log(f'archive codes done! file is saved to {archive_data}')
        except Exception as e:
            self.log(f'fail to make archive file with tar command because of {e}, try to use zip instead.')
            if os.path.exists(os.path.join(self.output_dir, "codes.zip")):
                system(f'rm {os.path.join(self.output_dir, "codes.zip")}', lambda x: self.log(x))
            system(f'cd {self.output_dir} &&  zip -r codes.zip codes', lambda x: self.log(x))
        finally:
            system(f'rm -rf {code_path}', lambda x: self.log(f'post-backing up: {x}'))

    def sync_log_to_remote(self, replace=False):
        import paramiko
        for target_machine_ind in range(len(MAIN_MACHINE_IP)):
            _ip, _port = map(lambda x: x[target_machine_ind], [
                MAIN_MACHINE_IP, MAIN_MACHINE_PORT,
            ])
            _user, _passwd, _log_path = MAIN_MACHINE_USER, MAIN_MACHINE_PASSWD, MAIN_MACHINE_LOG_PATH
            while _log_path.endswith('/'):
                _log_path = _log_path[:-1]
            while self.output_dir.endswith('/'):
                self.output_dir = self.output_dir[:-1]
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=_ip, port=_port, username=_user,
                            password=_passwd, timeout=5)
                self.log(f'ssh {_user}@{_ip} "mkdir -p {_log_path}"')
                _, stdout, _ = ssh.exec_command(f'mkdir -p {_log_path}')

                local_path = self.output_dir
                if self.logger_category is None:
                    remote_path = os.path.join(_log_path, self.log_name)
                else:
                    remote_path = os.path.join(_log_path, self.logger_category, self.log_name)

                process_dir = set()
                for root, _, files in os.walk(local_path, topdown=True):
                    for file in files:
                        full_path_in_local = os.path.join(root, file)
                        full_path_in_remote = full_path_in_local.replace(local_path, remote_path)
                        full_path_remote_dir = os.path.dirname(full_path_in_remote)
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
                for root, _, files in os.walk(local_path, topdown=False):
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
                                full_path_remote_dir = os.path.dirname(full_path_in_remote)
                                print(f'file {full_path_remote_dir} not found!!')
                                mkdir_cmd = f'mkdir -p {full_path_remote_dir}'
                                _, stdout, _ = ssh.exec_command(mkdir_cmd)
                                print(mkdir_cmd)
                t.close()
                ssh.close()
                self.log(f'transfer the log to {_user}@{_ip}:{_log_path} success!!!')
                break
            except Exception as e:
                import traceback
                self.log(traceback.print_exc())
                self.log(f'Error occur while transferring the log to {_ip}, {e}')

    def debug(self, info):
        self.log(f"[ DEBUG ]: {info}")

    def info(self, info):
        self.log(f"[ INFO ]: {info}")

    def error(self, info):
        self.log(f"[ ERROR ]: {info}")

    def log(self, *args, color=None, bold=True):
        super(Logger, self).log(*args, color=color, bold=bold)

    def log_dict(self, color=None, bold=False, **kwargs):
        for k, v in kwargs.items():
            super(Logger, self).log('{}: {}'.format(k, v), color=color, bold=bold)

    def log_dict_single(self, data, color=None, bold=False):
        for k, v in data.items():
            super(Logger, self).log('{}: {}'.format(k, v), color=color, bold=bold)

    def __call__(self, *args, **kwargs):
        self.log(*args, **kwargs)

    def log_tabular(self, key, val=None, tb_prefix=None, with_min_and_max=False, average_only=False, no_tb=False):
        if val is not None:
            super(Logger, self).log_tabular(key, val, tb_prefix, no_tb=no_tb)
        else:
            if key in self.current_data:
                self.logged_data.add(key)
                super(Logger, self).log_tabular(key if average_only else "Average"+key, np.mean(self.current_data[key]), tb_prefix, no_tb=no_tb)
                if not average_only:
                    super(Logger, self).log_tabular("Std" + key,
                                                    np.std(self.current_data[key]), tb_prefix, no_tb=no_tb)
                    if with_min_and_max:
                        super(Logger, self).log_tabular("Min" + key, np.min(self.current_data[key]), tb_prefix, no_tb=no_tb)
                        super(Logger, self).log_tabular('Max' + key, np.max(self.current_data[key]), tb_prefix, no_tb=no_tb)

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
    logger = Logger(log_name='log2')
    logger.log(122, '22', color='red', bold=False)
    data = {'a': 10, 'b': 11, 'c': 13}
    for i in range(100):
        for _ in range(10):
            for k in data:
                data[k] += 1
            logger.add_tabular_data(**data)
        logger.sync_log_to_remote()
        logger.log_tabular('a')
        logger.dump_tabular()
        time.sleep(1)





