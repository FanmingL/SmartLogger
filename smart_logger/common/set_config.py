from smart_logger.common import common_config
from smart_logger.common import experiment_config
from smart_logger.common import page_config
from smart_logger.common import plot_config


def set_common_config(**kwargs):
    for k, v in kwargs.items():
        if hasattr(common_config, k):
            setattr(common_config, k, v)


def set_experiment_config(**kwargs):
    for k, v in kwargs.items():
        if hasattr(experiment_config, k):
            setattr(experiment_config, k, v)


def set_experiment_customized_config(**kwargs):
    for k, v in kwargs:
        experiment_config.register_customized_value(k, v)


def set_page_config(**kwargs):
    for k, v in kwargs.items():
        if hasattr(page_config, k):
            setattr(page_config, k, v)


def set_plot_config(**kwargs):
    for k, v in kwargs.items():
        if hasattr(plot_config, k):
            setattr(plot_config, k, v)
