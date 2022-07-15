import sys
import os

import pandas as pd

import smart_logger.common.plot_config as plot_config
import json

import smart_logger.common.page_config as page_config
from smart_logger.util_logger.logger import Logger
from smart_logger.report.plotting import merger_to_short_name, list_embedding, standardize_string, make_merger_feature
from pathlib import Path
import fnmatch
import re


def get_config_path(config_name, user_name=None):
    if user_name is None:
        return os.path.join(page_config.CONFIG_PATH, config_name)
    else:
        return os.path.join(page_config.CONFIG_PATH, user_name, config_name)


def config_post_process(config):
    if config is None:
        return config
    if page_config.PLOTTING_SAVING_PATH_KEY in config:
        config[page_config.PLOTTING_SAVING_PATH_KEY] = page_config.FIGURE_PATH
    return config


def _default_config():
    return plot_config.global_plot_configs()


def default_config():
    config = _default_config()
    return config_post_process(config)


def save_config(config, file_name):
    full_file_name = get_config_path(file_name)
    # if os.path.exists(full_file_name):
    #     Logger.logger(f'file exists, you should remove it first!')
    #     return False
    Logger.logger(f'save config to {full_file_name}')
    try:
        os.makedirs(os.path.dirname(full_file_name), exist_ok=True)
        with open(full_file_name, 'w') as f:
            json.dump(config, f)
        Logger.logger(f'config save to {full_file_name} OK!')
        return True
    except Exception as e:
        Logger.logger(f'config save to {full_file_name} failed. Exception is {e}')
    return False


def _load_config(file_name):
    full_file_name = get_config_path(file_name)
    if os.path.exists(full_file_name):
        try:
            with open(full_file_name, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            Logger.logger(f"load from {full_file_name} failed, exception is {e}. The default config will be returned.")
            return None
    else:
        Logger.logger(f'file {full_file_name} not exists. The default config will be returned')
        return None


def has_config(file_name):
    return os.path.exists(get_config_path(file_name))

def load_config(file_name):
    _choose_config(config_name=file_name)
    config = _load_config(file_name)
    return config_post_process(config)

def delete_config_file(file_name):
    path_name = get_config_path(file_name)
    if os.path.exists(path_name):
        os.system(f'rm {path_name}')

def list_current_configs():
    total_config_files = os.listdir(page_config.CONFIG_PATH)
    total_config_files = [item for item in total_config_files if not item == 'default_config.json']
    return sorted(total_config_files)


def list_current_experiment():
    base_path = plot_config.PLOT_LOG_PATH
    total_folders = []
    for root, _, files in os.walk(base_path, topdown=True):
        for file in files:
            if file == 'progress.csv':
                if os.path.exists(os.path.join(root, 'parameter.json')) or \
                    os.path.exists(os.path.join(root, 'config', 'parameter.json')) or \
                        os.path.exists(os.path.join(root, 'config', 'running_config.json')):
                    folder_name = root[len(base_path) + 1:]
                    total_folders.append(root[len(base_path) + 1:])
                    # Logger.logger(f'append {folder_name}')
                    break
    return sorted(total_folders)


def standardize_merger_item(merger_item):
    if isinstance(merger_item, str):
        return standardize_string(merger_item)
    elif isinstance(merger_item, dict):
        res = {standardize_merger_item(k): v for k, v in merger_item.items()}
        return res
    elif isinstance(merger_item, list):
        res = [standardize_merger_item(item) for item in merger_item]
        return res


def _get_parameter(folder_name):
    base_path = plot_config.PLOT_LOG_PATH
    full_folder = os.path.join(base_path, folder_name)
    if not os.path.exists(full_folder) or not legal_path(full_folder):
        Logger.logger(f'{full_folder} not exists!')
        return None, None
    parameter_data = os.path.join(full_folder, 'config', 'parameter.json')
    running_config_data = os.path.join(full_folder, 'config', 'running_config.json')
    parameter_data_possible = os.path.join(full_folder, 'parameter.json')

    param = dict()
    if os.path.exists(parameter_data):
        with open(parameter_data, 'r') as f:
            param1 = json.load(f)
        if len(param1) == 0:
            Logger.logger(f'{parameter_data} not exists')
        param.update(param1)
    if os.path.exists(parameter_data_possible):
        with open(parameter_data_possible, 'r') as f:
            param_possible = json.load(f)
        param.update(param_possible)
    else:
        pass
        # Logger.logger(f'{parameter_data_possible} not founded')
    if os.path.exists(running_config_data):
        with open(running_config_data, 'r') as f:
            param2 = json.load(f)
        if len(param2) == 0:
            Logger.logger(f'{running_config_data} not exists')
        for k in page_config.CONSIDERED_RUNNING_CONFIG:
            if k in param2:
                param.update({k: param2[k]})
    if len(param) == 0:
        Logger.logger(f'no parameter found in {full_folder}')
        return None, None
    important_configs_dict = dict()

    if 'IMPORTANT_CONFIGS' in param:
        important_configs = param['IMPORTANT_CONFIGS']
        for iconfig in important_configs:
            if iconfig in param:
                important_configs_dict[iconfig] = param[iconfig]
    # Logger.logger(f'important params: {important_configs_dict}')
    return param, important_configs_dict


def get_parameter(folder_name):
    param, important_configs_dict = _get_parameter(folder_name)
    if param is None:
        return None, None, None, None, None, None
    dtree, full_path, name, filesize = generate_path_tree(folder_name)
    return param, dtree, full_path, name, filesize, important_configs_dict


def reformat_str(data):
    res = data.split('\n')
    return res


def reformat_dict(data):
    k_list = [k for k in data]
    k_list = sorted(k_list)
    res = []
    for k in k_list:
        res.append(f'{k}: {data[k]}')
    return res


class DirectionTree(object):
    def __init__(self, pathname='.'):
        super(DirectionTree, self).__init__()
        self.pathname = Path(pathname)
        self.root_name = pathname
        self.tree = ''
        self.full_path = []
        self.name = []
        self.filesize = []

    @staticmethod
    def getfile_size(filename):
        fsize = os.path.getsize(filename)
        if fsize < 1024:
            return f'{fsize}B'
        elif fsize < 1024 * 1024:
            return f'{round(fsize / 1024, 2)}KB'
        elif fsize < 1024 * 1024 * 1024:
            return f'{round(fsize / 1024 / 1024, 2)}MB'
        else:
            return f'{round(fsize / 1024 / 1024 / 1024, 2)}GB'

    def generate_tree(self, n=0):
        if self.pathname.is_file():
            # file is able to downloads
            self.tree += '    |' * n + '-' * 4 + self.pathname.name + '\n'
            self.full_path += [str(self.pathname.relative_to(os.path.dirname(self.root_name)))]
            self.name.append(str(self.pathname.name))
            self.filesize.append(DirectionTree.getfile_size(str(self.pathname)))
        elif self.pathname.is_dir():
            self.full_path += [None]
            self.name.append(str(self.pathname.name))
            self.filesize.append(0)
            prefix = '    |' * n + '-' * 4
            if n == 0:
                prefix = ''
            self.tree += prefix + \
                         str(self.pathname.relative_to(self.pathname.parent)) + '/' + '\n'

            for cp in self.pathname.iterdir():
                self.pathname = Path(cp)
                self.generate_tree(n + 1)


def generate_path_tree(folder):
    base_path = plot_config.PLOT_LOG_PATH
    full_folder = os.path.join(base_path, folder)
    dtree = DirectionTree(full_folder)
    dtree.generate_tree()
    # Logger.logger(dtree.tree)
    # Logger.logger(dtree.full_path)
    return dtree.tree, dtree.full_path, dtree.name, dtree.filesize


def legal_path(p: str):
    base_path = plot_config.PLOT_LOG_PATH
    rel = os.path.relpath(p, base_path)
    if rel.startswith('..'):
        return False
    return True


def make_config_type(config: dict):
    config_type = dict()
    for k, v in config.items():
        if isinstance(v, bool):
            config_type[k] = "bool"
        elif isinstance(v, float):
            config_type[k] = "float"
        elif isinstance(v, tuple):
            config_type[k] = "tuple"
        elif isinstance(v, int):
            config_type[k] = "int"
        elif isinstance(v, dict):
            config_type[k] = "dict"
        elif isinstance(v, list):
            if len(v) == 0:
                config_type[k] = "list"
            else:
                if isinstance(v[0], list):
                    config_type[k] = "double_list"
                elif isinstance(v[0], dict):
                    config_type[k] = "list_dict"
                else:
                    config_type[k] = "list"
        elif isinstance(v, str):
            config_type[k] = "str"
        else:
            config_type[k] = "str"
        # Logger.logger(f'{v} is classified to {config_type[k]}')
    return config_type


def get_record_data_item(folder_name):
    full_folder = os.path.join(plot_config.PLOT_LOG_PATH, folder_name)
    if 'progress.csv' not in os.listdir(full_folder):
        return []
    data_path = os.path.join(full_folder, 'progress.csv')
    try:
        data = pd.read_csv(data_path)
        value_list = list(data.keys())
        if len(value_list) == 1:
            data = pd.read_table(data_path)
            value_list = list(data.keys())

        return value_list
    except Exception as e:
        Logger.logger(f'read csv from {data_path} failed, because {e}')
    return []


def config_to_short_name(config, data_merger, short_name_from_config):
    elements = []
    for k in data_merger:
        if k in config:
            elements.append(make_merger_feature(k,  config[k]))
    short_name_origin = list_embedding(elements)
    short_name = merger_to_short_name(elements, short_name_from_config)
    return short_name_origin, short_name


chosen_config_name_dict = dict()


def _choose_config(config_name):
    if config_name in chosen_config_name_dict:
        return
    chosen_config_name_dict[config_name] = True
    config_new = load_config(config_name)
    for k, v in config_new.items():
        if hasattr(plot_config, k):
            setattr(plot_config, k, v)
    _default_config = load_config('default_config.json')
    k_set_mismatch = False
    for k in _default_config:
        if k not in config_new:
            config_new[k] = _default_config[k]
            k_set_mismatch = True
    deleted_keys = set()
    for k in config_new:
        if k not in _default_config:
            deleted_keys.add(k)
    if len(deleted_keys) > 0:
        k_set_mismatch = True
        config_new = {k: v for k, v in config_new.items() if k not in deleted_keys}
    for k, v in _default_config['DESCRIPTION'].items():
        if k not in config_new['DESCRIPTION'] or not config_new['DESCRIPTION'][k] == v:
            config_new['DESCRIPTION'][k] = v
            k_set_mismatch = True
    if not len(config_new['DATA_IGNORE_PROPERTY']) == len(config_new['DATA_IGNORE']):
        print(f'DATA_IGNORE_PROPERTY does not valid, reinit it')
        config_new['DATA_IGNORE_PROPERTY'] = []
        for item in config_new['DATA_IGNORE']:
            config_new['DATA_IGNORE_PROPERTY'].append({k: {} for k in item})
    if not len(config_new['DATA_SELECT_PROPERTY']) == len(config_new['DATA_SELECT']):
        print(f'DATA_SELECT_PROPERTY does not valid, reinit it')
        config_new['DATA_SELECT_PROPERTY'] = []
        for item in config_new['DATA_SELECT']:
            config_new['DATA_SELECT_PROPERTY'].append({k: {} for k in item})
    if k_set_mismatch:
        save_config(config_new, config_name)

def can_ignore(config, data_ignore, data_merger, data_ignore_property):
    if len(data_ignore) == 0:
        return False
    if config is None:
        return True
    match_ignore = False
    short_name_origin, _ = config_to_short_name(config, data_merger, {})
    for data_ignore_ind, data_ignore_item in enumerate(data_ignore):
        match_ignore = True
        for k, v in data_ignore_item.items():
            require_re_check = isinstance(v, str) and len(data_ignore_property) > data_ignore_ind \
                               and k in data_ignore_property[data_ignore_ind] \
                               and 'manual' in data_ignore_property[data_ignore_ind][k] \
                               and data_ignore_property[data_ignore_ind][k]['manual']
            if k == '__SHORT_NAME__':
                if not standardize_string(v) == standardize_string(short_name_origin):
                    match_ignore = False
                    break
            elif k not in config or (not require_re_check and not v == config[k]):
                match_ignore = False
                break
            elif require_re_check:
                try:
                    if not fnmatch.fnmatch(config[k], v):
                        match_ignore = False
                        break
                except Exception as e:
                    if not v == config[k]:
                        match_ignore = False
                        break
        if match_ignore:
            break
    if match_ignore:
        return True
    return False


def can_preserve(config, data_select, data_merger, data_select_property):
    if len(data_select) == 0:
        return False
    if config is None:
        return False
    match_select = False
    short_name_origin, _ = config_to_short_name(config, data_merger, {})
    for data_select_ind, data_select_item in enumerate(data_select):
        match_select = True

        for k, v in data_select_item.items():
            require_re_check = isinstance(v, str) and len(data_select_property) > data_select_ind \
                               and k in data_select_property[data_select_ind] \
                               and 'manual' in data_select_property[data_select_ind][k] \
                               and data_select_property[data_select_ind][k]['manual']
            if k not in config or (not require_re_check and not v == config[k]):
                match_select = False
                break
            elif require_re_check:
                try:
                    if not fnmatch.fnmatch(config[k], v):
                        match_select = False
                        break
                except Exception as e:
                    if not v == config[k]:
                        match_select = False
                        break
        if match_select:
            break
    return match_select


def analyze_experiment(need_ignore=False, data_ignore=None, need_select=False,
                       data_select=None, data_merge=None, data_short_name_dict=None,
                       data_ignore_property=None, data_select_property=None):
    all_folders = list_current_experiment()
    folder_ignore = []
    if need_ignore:
        if data_ignore is None:
            data_ignore = plot_config.DATA_IGNORE
        if data_ignore_property is None:
            data_ignore_property = plot_config.DATA_IGNORE_PROPERTY
    else:
        data_ignore = []
        data_ignore_property = []
    if need_select:
        if data_select is None:
            data_select = plot_config.DATA_SELECT
        if data_select_property is None:
            data_select_property = plot_config.DATA_SELECT_PROPERTY
    else:
        data_select = []
        data_select_property = []
    data_short_name_dict = {} if data_short_name_dict is None else data_short_name_dict
    folder_list = []
    config_list = []
    alg_idxs = []

    config_list_ignore = []
    alg_idxs_ignore = []

    nick_name_list = []
    nick_name_ignore_list = []
    config_list_ignore = []
    short_name_to_ind = dict()
    short_name_to_ind_ignore = dict()
    for folder in all_folders:
        config, important_config = _get_parameter(folder)
        if config is None:
            continue
        ignore_file = False
        if need_ignore and can_ignore(config, data_ignore, data_merge, data_ignore_property):
            folder_ignore.append(folder)
            config_list_ignore.append(config)
            ignore_file = True
        if not ignore_file and need_select and not can_preserve(config, data_select, data_merge, data_select_property):
            folder_ignore.append(folder)
            config_list_ignore.append(config)
            ignore_file = True
        short_name, short_name_nick = config_to_short_name(config, data_merge, data_short_name_dict)
        if not ignore_file:
            nick_name_list.append(short_name_nick)
            if short_name not in short_name_to_ind:
                short_name_to_ind[short_name] = len(short_name_to_ind)
            alg_idxs.append(short_name_to_ind[short_name])
            folder_list.append(folder)
            config_list.append(config)
        else:
            nick_name_ignore_list.append(short_name_nick)
            if short_name not in short_name_to_ind_ignore:
                short_name_to_ind_ignore[short_name] = len(short_name_to_ind_ignore)
            alg_idxs_ignore.append(short_name_to_ind_ignore[short_name])
    def stat_config(_config_list):
        _possible_config = dict()
        for config in _config_list:
            for k, v in config.items():
                if k not in _possible_config:
                    _possible_config[k] = set()
                if isinstance(v, list):
                    v = tuple(v)
                _possible_config[k].add(v)
        _selected_choices = dict()
        for k in _possible_config:
            _possible_config[k] = list(_possible_config[k])
        for k, v in _possible_config.items():
            if len(v) > 1:
                _selected_choices[k] = list(v)
        return _possible_config, _selected_choices

    possible_config, selected_choices = stat_config(config_list)
    possible_config_ignore, selected_choices_ignore = stat_config(config_list_ignore)
    Logger.logger(f'short name to ind: {short_name_to_ind}')
    sorted_res = [*zip(*sorted([*zip(alg_idxs, folder_list, nick_name_list)], key=lambda x: x[0]))]
    sorted_res_ignore = [*zip(*sorted([*zip(alg_idxs_ignore, folder_ignore, nick_name_ignore_list)], key=lambda x: x[0]))]
    if len(sorted_res) > 0:
        alg_idxs, folder_list, nick_name_list = sorted_res
    if len(sorted_res_ignore) > 0:
        alg_idxs_ignore, folder_ignore, nick_name_ignore_list = sorted_res_ignore
    return folder_list, folder_ignore, selected_choices, possible_config_ignore, selected_choices_ignore, alg_idxs_ignore, folder_ignore, nick_name_ignore_list, alg_idxs, possible_config, short_name_to_ind, nick_name_list
    # for


def diff_to_default(config):
    default_conf = load_config('default_config.json')

    default_missing_key = []
    current_missing_key = []
    differences = []
    if default_conf is None:
        return default_missing_key, current_missing_key, differences
    for k in config:
        if k not in default_conf:
            default_missing_key.append(k)
    for k in default_conf:
        if k not in config:
            current_missing_key.append(k)
        else:
            default_value = str(default_conf[k])
            current_value = str(config[k])
            if not default_value == current_value:
                differences.append((k, default_value, current_value))
    return default_missing_key, current_missing_key, differences

def main():
    analyze_experiment(True)


if __name__ == '__main__':
    Logger.init_global_logger(base_path=page_config.WEB_RAM_PATH, log_name="exp_logs")

    main()
