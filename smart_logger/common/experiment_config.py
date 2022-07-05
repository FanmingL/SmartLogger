# 配置开始
from multiprocessing import current_process

# 关键的参数名，这些参数会写到日志的名称中
IMPORTANT_CONFIGS = ['env_name', 'policy_lr', 'seed']
# 存日志时的后缀名，如果在将name_suffix设成了一个参数，那会优先用name_suffix
SHORT_NAME_SUFFIX = 'INIT_TEST'
# 本次训练目的的简要描述
EXPERIMENT_TARGET = "初始化训练"

EXPERIMENT_COMMON_PARAMETERS = dict(
    demo_variable='test'
)
# 配置结束


__REWRITE = False
__WARN_DICT = {}


def _is_main_process():
    return current_process().name == 'MainProcess'


def _check_multiprocess():
    if not _is_main_process() and not __REWRITE and 'mutiprocess' not in __WARN_DICT:
        print(f'[ WARN ] [_check_multiprocess in smart_logger.common.experiment_config.py] You are trying to '
              f'query config in a sub-process without rewriting it with the data in the parent process. '
              f'Remember to call set_xxxx_config '
              f'[smart_logger.common.serialize_config or smart_logger.common.set_config] first in the subprocess!!')
        __WARN_DICT['mutiprocess'] = True


def _get_global_configs_exp(things):
    res = dict()
    for k, v in things:
        if not k.startswith('__') and not hasattr(v, '__call__') and 'module' not in str(type(v)):
            res[k] = v
    return res


def global_configs_exp(things=[*locals().items()]):
    return _get_global_configs_exp(things)


def _to_yaml(file_name):
    _check_multiprocess()
    data = {k: getattr(locals(), k) for k in global_configs_exp()}
    import yaml
    yaml.dump(data, open(file_name, 'w'))


def _to_json(file_name):
    _check_multiprocess()
    data = {k: getattr(locals(), k) for k in global_configs_exp()}
    import json
    json.dump(data, open(file_name, 'w'))


def register_customized_value(k, v):
    EXPERIMENT_COMMON_PARAMETERS[k] = v


def has_customized_value(k):
    return k in EXPERIMENT_COMMON_PARAMETERS


def get_customized_value(k):
    _check_multiprocess()
    return EXPERIMENT_COMMON_PARAMETERS[k]
# ALL_CONFIGS = get_global_configs([*locals().items()])

