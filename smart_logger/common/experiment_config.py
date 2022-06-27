# 配置开始

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


def get_global_configs_exp(things):
    res = dict()
    for k, v in things:
        if not k.startswith('__') and not hasattr(v, '__call__') and 'module' not in str(type(v)):
            res[k] = v
    return res


def global_configs_exp(things=[*locals().items()]):
    return get_global_configs_exp(things)


def _to_yaml(file_name):
    data = global_configs_exp()
    import yaml
    yaml.dump(data, open(file_name, 'w'))


def _to_json(file_name):
    data = global_configs_exp()
    import json
    json.dump(data, open(file_name, 'w'))


def register_customized_value(k, v):
    EXPERIMENT_COMMON_PARAMETERS[k] = v


def get_customized_value(k):
    return EXPERIMENT_COMMON_PARAMETERS.get(k)
# ALL_CONFIGS = get_global_configs([*locals().items()])

