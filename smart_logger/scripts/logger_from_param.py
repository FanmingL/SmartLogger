import os

from smart_logger.util_logger.logger import Logger
from smart_logger.parameter.ParameterTemplate import ParameterTemplate


def logger_from_param(parameter: ParameterTemplate, save_config=True, **logger_kwargs):
    """
    从parameter构造logger的函数. 推荐调用方式:

    from smart_logger import logger_from_param
    logger, parameter = logger_from_param(Parameter())

    或者

    parameter = Parameter(config_path='xxx')
    parameter.xxx = xxxxx
    ...
    logger, _ = logger_from_param(parameter)
    """
    logger = Logger(log_name=parameter.short_name, log_signature=parameter.signature, **logger_kwargs)
    # 设置parameter的logger
    parameter.set_logger(logger)
    # 设置parameter的保存路径
    parameter.set_config_path(os.path.join(logger.output_dir, 'config'))
    # 保存parameter
    if save_config:
        parameter.save_config()
    return logger, parameter
