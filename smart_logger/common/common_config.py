import os.path as osp
import os
# 配置开始，本文件存放与实验内容无关的配置
# 我们把日志文件夹同步到远程时，会放在远程的/home/luofm/Data/LOG_DIR_BACKING_NAME路径下
LOG_DIR_BACKING_NAME = 'RAMRLLog'

# 远程日志备份相关
# 远程服务器的IP，这里提供了一个list，是因为一个机器有多个IP存在，如果一个IP传送数据失败了，就尝试往另一个该机器对应的IP传送
MAIN_MACHINE_IP = ["127.0.0.1"]
# 远程服务器的端口list
MAIN_MACHINE_PORT = [22]
# 远程服务器的登录账号
MAIN_MACHINE_USER = "user_name"
# 远程服务器的登录密码
MAIN_MACHINE_PASSWD = "xxxxxxx"
# 远程工作目录
WORKSPACE_PATH = "/home/luofm/Data"
# 将日志文件发到远程服务器的哪一个路径下
MAIN_MACHINE_LOG_PATH = f"{WORKSPACE_PATH}/{LOG_DIR_BACKING_NAME}"

# 本地日志配置
# 本地日志文件夹名
LOG_FOLDER_NAME = 'logfile'
# 本地日志备份文件夹名
LOG_FOLDER_NAME_BK = 'logfile_bk'

# 进行代码备份时，以此开头的文件或者文件夹不备份
BACKUP_IGNORE_HEAD = ['__p', '.']
# 进行代码备份时，有以下关键词的文件或者文件夹不备份
BACKUP_IGNORE_KEY = [LOG_FOLDER_NAME, LOG_FOLDER_NAME_BK, 'baselines']
# 进行代码备份时，以此结尾的文件或者文件夹不备份
BACKUP_IGNORE_TAIL = []
# 基础路径
BASE_PATH = None
# 配置结束


def get_global_configs(things):
    res = dict()
    for k, v in things:
        if not k.startswith('__') and not hasattr(v, '__call__') and 'module' not in str(type(v)):
            res[k] = v
    return res


def global_configs(things=[*locals().items()]):
    return get_global_configs(things)


def get_base_path():
    if BASE_PATH is None:
        return osp.dirname(osp.dirname(osp.dirname(osp.abspath(__file__))))
    return BASE_PATH


def get_log_base_path():
    return get_base_path()


def _to_yaml(file_name):
    data = global_configs()
    import yaml
    yaml.dump(data, open(file_name, 'w'))


def _to_json(file_name):
    data = global_configs()
    import json
    json.dump(data, open(file_name, 'w'))


def system(cmd, print_func=None):
    if print_func is None:
        print(cmd)
    else:
        print_func(cmd)
    os.system(cmd)
