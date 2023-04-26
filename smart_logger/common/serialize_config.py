import json
import os

import yaml

from smart_logger.common import common_config
from smart_logger.common import experiment_config
from smart_logger.common.set_config import set_common_config, set_experiment_config


def save_all():
    path = 'configs'
    os.makedirs(path, exist_ok=True)
    common_config._to_yaml(os.path.join(path, 'common_config.yaml'))
    experiment_config._to_yaml(os.path.join(path, 'experiment_config.yaml'))
    common_config._to_json(os.path.join(path, 'common_config.json'))
    experiment_config._to_json(os.path.join(path, 'experiment_config.json'))


def serialize_common_config_from_yaml(path):
    config = yaml.load(open(path, 'r'), yaml.FullLoader)
    set_common_config(**config)


def serialize_experiment_config_from_yaml(path):
    config = yaml.load(open(path, 'r'), yaml.FullLoader)
    set_experiment_config(**config)


def serialize_common_config_from_json(path):
    config = json.load(open(path, 'r'))
    set_common_config(**config)


def serialize_experiment_config_from_json(path):
    config = json.load(open(path, 'r'))
    set_experiment_config(**config)


def init_config(common_config_file=None, experiment_config_file=None, base_path=None):
    if base_path is not None:
        if not common_config_file.startswith('/'):
            common_config_file = os.path.join(base_path, common_config_file)
        if not experiment_config_file.startswith('/'):
            experiment_config_file = os.path.join(base_path, experiment_config_file)
    if common_config_file is not None:
        if common_config_file.endswith('json'):
            serialize_common_config_from_json(common_config_file)
        elif common_config_file.endswith('yaml'):
            serialize_common_config_from_yaml(common_config_file)
        else:
            raise NotImplemented(f'common config file {common_config_file} does not belong to [json, yaml].')
    if experiment_config_file is not None:
        if experiment_config_file.endswith('json'):
            serialize_experiment_config_from_json(experiment_config_file)
        elif experiment_config_file.endswith('yaml'):
            serialize_experiment_config_from_yaml(experiment_config_file)
        else:
            raise NotImplemented(f'experiment config file {experiment_config_file} does not belong to [json, yaml].')
    if base_path is not None:
        common_config.BASE_PATH = base_path


def get_total_config():
    config = dict()
    config['common'] = {k: getattr(common_config, k) for k in common_config.global_configs()}
    config['experiment'] = {k: getattr(experiment_config, k) for k in experiment_config.global_configs_exp()}
    return config


def set_total_config(config):
    set_common_config(**config['common'])
    set_experiment_config(**config['experiment'])


if __name__ == '__main__':
    save_all()
