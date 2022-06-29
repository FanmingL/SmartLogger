import os, sys
import argparse
import json
import socket
from smart_logger.common import common_config
from smart_logger.common import experiment_config
import os.path as osp
from datetime import datetime
import hashlib


class ParameterTemplate:
    def __init__(self, config_path=None, debug=False):
        self.base_path = self.get_base_path()
        self.debug = debug
        self.experiment_target = experiment_config.EXPERIMENT_TARGET
        self.DEFAULT_CONFIGS = {k: getattr(common_config, k) for k in common_config.global_configs()}
        self.DEFAULT_CONFIGS_EXP = {k: getattr(experiment_config, k) for k in experiment_config.global_configs_exp()}
        self.arg_names = []
        self.host_name = "my_machine"
        self.ip = "127.0.0.1"
        for _ in range(5):
            try:
                self.host_name = socket.gethostname()
                self.ip = socket.gethostbyname(self.host_name)
            except Exception as e:
                pass
        self.exec_time = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        self.commit_id = self.get_commit_id()
        self.log_func = print
        self.json_name = 'parameter.json'
        self.json_name_version = 'running_config.json'
        self.txt_name = 'full_description.txt'
        if config_path:
            self.config_path = config_path
        else:
            self.info('use default config path')
            self.config_path = osp.join(common_config.get_base_path(), 'logfile', 'config')
        if config_path:
            self.load_config()
        else:
            self.args = self.parse()
            self.arg_names = [item for item in vars(self.args)]
            self.apply_vars(self.args)

    def info(self, info):
        self.log_func(info)

    def set_logger(self, logger):
        self.log_func = logger

    @staticmethod
    def get_base_path():
        return common_config.get_base_path()

    def set_config_path(self, config_path):
        self.config_path = config_path

    @staticmethod
    def important_configs():
        res = experiment_config.IMPORTANT_CONFIGS
        return res

    def apply_vars(self, args):
        for name in self.arg_names:
            setattr(self, name, getattr(args, name))

    def make_dict(self):
        res = {}
        for name in self.arg_names:
            res[name] = getattr(self, name)
        return res

    def get_version_dict(self):
        res = {}
        res['description'] = self.experiment_target
        res['exec_time'] = self.exec_time
        res['commit_id'] = self.commit_id
        res['host_name'] = self.host_name
        res['ip'] = self.ip
        for k, v in self.DEFAULT_CONFIGS.items():
            res[k] = v
        for k, v in self.DEFAULT_CONFIGS_EXP.items():
            if k == 'EXPERIMENT_COMMON_PARAMETERS':
                for k2, v2 in self.DEFAULT_CONFIGS_EXP[k].items():
                    res[k2] = v2
        return res

    def parse(self):
        parser = argparse.ArgumentParser(description=experiment_config.EXPERIMENT_TARGET)

        self.env_name = 'Hopper-v2'
        parser.add_argument('--env_name', type=str, default=self.env_name, metavar='N',
                            help="name of the environment to run")

        self.sac_update_interval = 1
        parser.add_argument('--sac_update_interval', type=int, default=self.sac_update_interval, metavar='N',
                            help="sample number per sac update.")

        self.policy_lr = 3e-4
        parser.add_argument('--policy_lr', type=float, default=self.policy_lr, metavar='N',
                            help="learning rate of the policy.")

        self.backing_log = False
        parser.add_argument('--backing_log', action='store_true',
                            help='whether backing up the log files to a remote machine.')

        return parser.parse_args()

    def get_vars_description(self):
        var = ''
        important_config = self.important_configs()
        for name in self.arg_names:
            if name in important_config:
                var += f'**{name}**: {getattr(self, name)}\n'
            else:
                var += f'{name}: {getattr(self, name)}\n'
        for name in self.DEFAULT_CONFIGS:
            var += f'{name}: {self.DEFAULT_CONFIGS[name]}\n'
        for name in self.DEFAULT_CONFIGS_EXP:
            var += f'{name}: {self.DEFAULT_CONFIGS_EXP[name]}\n'
        return var

    def get_experiment_description(self):
        description = f"本机{self.host_name}, ip为{self.ip}\n"
        description += f"目前实验目的为{self.experiment_target}\n"
        description += f"实验简称: {self.short_name}\n"
        description += f"运行开始时间: {self.exec_time}\n"
        description += f"commit id: {self.commit_id}\n"
        var = self.get_vars_description()
        return description + var

    @property
    def signature(self):
        var = self.get_vars_description()
        md5_hash = hashlib.md5(var.encode())
        return md5_hash.hexdigest()

    def __str__(self):
        return self.get_experiment_description()

    def save_config(self):
        self.info(f'save json config to {os.path.join(self.config_path, self.json_name)}')
        os.makedirs(self.config_path, exist_ok=True)
        with open(os.path.join(self.config_path, self.json_name), 'w') as f:
            things = self.make_dict()
            ser = json.dumps(things)
            f.write(ser)
        with open(os.path.join(self.config_path, self.json_name_version), 'w') as f:
            things = self.get_version_dict()
            ser = json.dumps(things)
            f.write(ser)
        self.info(f'save readable config to {os.path.join(self.config_path, self.txt_name)}')
        with open(os.path.join(self.config_path, self.txt_name), 'w') as f:
            print(self, file=f)

    def load_config(self):
        self.info(f'load json config from {os.path.join(self.config_path, self.json_name)}')
        with open(os.path.join(self.config_path, self.json_name), 'r') as f:
            ser = json.load(f)
        for k, v in ser.items():
            setattr(self, k, v)
            self.arg_names.append(k)

    @property
    def differences(self):
        if not os.path.exists(os.path.join(self.config_path, self.json_name)):
            return None
        with open(os.path.join(self.config_path, self.json_name), 'r') as f:
            ser = json.load(f)
        differences = []
        for k, v in ser.items():
            if not hasattr(self, k):
                differences.append(k)
            else:
                v2 = getattr(self, k)
                if not v2 == v:
                    differences.append(k)
        return differences

    def check_identity(self, need_description=False, need_exec_time=False):
        if not os.path.exists(os.path.join(self.config_path, self.json_name)):
            self.info(f'{os.path.join(self.config_path, self.json_name)} not exists')
            return False
        with open(os.path.join(self.config_path, self.json_name), 'r') as f:
            ser = json.load(f)
        flag = True
        for k, v in ser.items():
            if not k == 'description' and not k == 'exec_time':
                if not hasattr(self, k):
                    flag = False
                    return flag
                v2 = getattr(self, k)
                if not v2 == v:
                    flag = False
                    return flag
        if need_description:
            if not self.experiment_target == ser['description']:
                flag = False
                return flag
        if need_exec_time:
            if not self.exec_time == ser['exec_time']:
                flag = False
                return flag
        return flag

    @property
    def short_name(self):
        name = ''
        for item in self.important_configs():
            if not hasattr(self, item):
                raise NameError(f'Parameter does not have \"{item}\"!!')
            value = getattr(self, item)
            if len(name) > 0:
                name += '_'
            if isinstance(value, str):
                name += value
            elif isinstance(value, bool) and value:
                name += item
            else:
                name += f'{item}_{value}'
        if hasattr(self, 'information') and not getattr(self, 'information') == 'None':
            name += '-{}'.format(getattr(self, 'information'))
        else:
            name += '-{}'.format(experiment_config.SHORT_NAME_SUFFIX)
        if self.debug:
            name += '-debug'

        return name

    @property
    def suffix(self):
        suffix = None
        if hasattr(self, 'name_suffix') and not getattr(self, 'name_suffix') == 'None':
            suffix = f'{self.name_suffix}'
        elif not len(experiment_config.SHORT_NAME_SUFFIX) == 0:
            suffix = f'{experiment_config.SHORT_NAME_SUFFIX}'
        return suffix

    def get_commit_id(self):
        base_path = common_config.get_base_path()
        cmd = f'cd {base_path} && git log'
        commit_id = None
        try:
            with os.popen(cmd) as f:
                line = f.readline()
                words = line.split(' ')
                commit_id = words[-1][:-1]
        except Exception as e:
            self.info(f'Error occurs while fetching commit id!!! {e}')
        return commit_id


