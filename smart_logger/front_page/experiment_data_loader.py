import os
import fnmatch
import json
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import shutil
import smart_logger.common.page_config as page_config
import smart_logger.common.plot_config as plot_config
from smart_logger.report.plotting import merger_to_short_name, list_embedding, standardize_string, make_merger_feature, _check_parent_alive
from smart_logger.util_logger.logger import Logger
import pickle
import threading

def generate_random_string(length):
    ascii_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    random_string = ''.join(random.choice(ascii_letters) for _ in range(length))
    return random_string

def safe_dump(obj, file_name):
    cache_filename = f'{file_name}____{generate_random_string(10)}'
    try:
        with open(cache_filename, 'w') as f:
            json.dump(obj, f)
        shutil.move(cache_filename, file_name)
    except Exception as e:
        import traceback
        traceback.print_exc()
    if os.path.exists(cache_filename):
        Logger.local_log(f'Error: {cache_filename} existing!!!!')
        os.remove(cache_filename)

def safe_pickle_dump(obj, file_name):
    cache_filename = f'{file_name}____{generate_random_string(10)}'
    try:
        with open(cache_filename, 'wb') as f:
            pickle.dump(obj, f)
        shutil.move(cache_filename, file_name)
    except Exception as e:
        import traceback
        traceback.print_exc()
    if os.path.exists(cache_filename):
        Logger.local_log(f'Error: {cache_filename} existing!!!!')
        os.remove(cache_filename)

def get_config_path(config_name, user_name=None):
    if user_name is None:
        return os.path.join(page_config.CONFIG_PATH, config_name)
    else:
        return os.path.join(page_config.CONFIG_PATH, user_name, config_name)


def config_post_process(config):
    if config is None:
        return config
    if config is not None and page_config.PLOTTING_SAVING_PATH_KEY in config:
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
    #     Logger.local_log(f'file exists, you should remove it first!')
    #     return False
    Logger.local_log(f'save config to {full_file_name}')
    try:
        os.makedirs(os.path.dirname(full_file_name), exist_ok=True)
        for k in plot_config.FIXED_PARAMETER:
            if k in config:
                config.pop(k)
        safe_dump(config, full_file_name)
        Logger.local_log(f'config save to {full_file_name} OK!')
        return True
    except Exception as e:
        Logger.local_log(f'config save to {full_file_name} failed. Exception is {e}')
    return False

def load_data_cache(config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'data_cache', config_name)
    if not os.path.exists(local_data_path):
        data = dict()
    else:
        data = json.load(open(local_data_path, 'r'))
    return data

def save_data_cache(data, config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'data_cache', config_name)
    os.makedirs(os.path.dirname(local_data_path), exist_ok=True)
    safe_dump(data, local_data_path)

def load_config_cache(config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'data_config_cache', config_name)
    if not os.path.exists(local_data_path):
        data = dict()
    else:
        data = json.load(open(local_data_path, 'r'))
    return data

def save_plotting_data_cache(data, config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'plotting_data_cache', config_name)
    os.makedirs(os.path.dirname(local_data_path), exist_ok=True)
    safe_pickle_dump(data, local_data_path)

def load_plotting_data_cache(config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'plotting_data_cache', config_name)
    data = None
    try:
        data = pickle.load(open(local_data_path, 'rb'))
    except Exception as e:
        Logger.local_log(f'load from {local_data_path} failed')
    return data


def save_config_cache(data, config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'data_config_cache', config_name)
    os.makedirs(os.path.dirname(local_data_path), exist_ok=True)
    safe_dump(data, local_data_path)

def load_table_cache(config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'table_cache', config_name)
    if not os.path.exists(local_data_path):
        data = dict()
    else:
        data = json.load(open(local_data_path, 'r'))
    return data

def save_table_cache(data, config_name):
    local_data_path = os.path.join(page_config.WEB_RAM_PATH, 'table_cache', config_name)
    os.makedirs(os.path.dirname(local_data_path), exist_ok=True)
    safe_dump(data, local_data_path)

def _load_config(file_name):
    full_file_name = get_config_path(file_name)
    if os.path.exists(full_file_name):
        try:
            with open(full_file_name, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            Logger.local_log(f"load from {full_file_name} failed, exception is {e}. The default config will be returned.")
            return None
    else:
        Logger.local_log(f'file {full_file_name} not exists. The default config will be returned')
        return None


def has_config(file_name):
    return os.path.exists(get_config_path(file_name))


def load_config(file_name):
    _choose_config(config_name=file_name)
    config = _load_config(file_name)
    if isinstance(config, dict):
        for k in plot_config.FIXED_PARAMETER:
            if k in config:
                config.pop(k)
    return config_post_process(config)

def get_config_modified_timestamp(file_name):
    full_file_name = get_config_path(file_name)
    if not os.path.exists(full_file_name):
        return -1
    else:
        return os.path.getmtime(full_file_name)


def delete_config_file(file_name):
    path_name = get_config_path(file_name)
    if os.path.exists(path_name):
        os.system(f'rm \"{path_name}\"')


def list_current_configs():
    total_config_files = os.listdir(page_config.CONFIG_PATH)
    total_config_files = [item for item in total_config_files if not item == 'default_config.json' and
                          os.path.isfile(os.path.join(page_config.CONFIG_PATH, item))]
    return sorted(total_config_files)


def list_current_experiment():
    base_path = plot_config.PLOT_LOG_PATH
    total_folders = []
    for root, _, files in os.walk(base_path, topdown=True, followlinks=True):
        for file in files:
            if file == 'progress.csv':
                if os.path.exists(os.path.join(root, 'parameter.json')) or \
                        os.path.exists(os.path.join(root, 'config', 'parameter.json')) or \
                        os.path.exists(os.path.join(root, 'config', 'running_config.json')):
                    total_folders.append(root[len(base_path) + 1:])
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
        Logger.local_log(f'{full_folder} not exists!')
        return None, None
    parameter_data = os.path.join(full_folder, 'config', 'parameter.json')
    running_config_data = os.path.join(full_folder, 'config', 'running_config.json')
    parameter_data_possible = os.path.join(full_folder, 'parameter.json')

    param = dict()
    if os.path.exists(parameter_data):
        with open(parameter_data, 'r') as f:
            try:
                param1 = json.load(f)
            except Exception as e:
                Logger.local_log(f'load param1: {parameter_data} fail')
                param1 = dict()
        if len(param1) == 0:
            Logger.local_log(f'{parameter_data} not exists')
        param.update(param1)
    if os.path.exists(parameter_data_possible):
        with open(parameter_data_possible, 'r') as f:
            try:
                param_possible = json.load(f)
            except Exception as e:
                Logger.local_log(f'load parameter: {parameter_data_possible} fail')
                param_possible = dict()
        param.update(param_possible)
    else:
        pass
        # Logger.local_log(f'{parameter_data_possible} not founded')
    if os.path.exists(running_config_data):
        with open(running_config_data, 'r') as f:
            try:
                param2 = json.load(f)
            except Exception as e:
                Logger.local_log(f'load param2: {running_config_data} fail')
                param2 = dict()
        if len(param2) == 0:
            Logger.local_log(f'{running_config_data} not exists')
        for k in page_config.CONSIDERED_RUNNING_CONFIG:
            if k in param2:
                param.update({k: param2[k]})
    if len(param) == 0:
        Logger.local_log(f'no parameter found in {full_folder}')
        return None, None
    important_configs_dict = dict()

    if 'IMPORTANT_CONFIGS' in param:
        important_configs = param['IMPORTANT_CONFIGS']
        for iconfig in important_configs:
            if iconfig in param:
                important_configs_dict[iconfig] = param[iconfig]
    # Logger.local_log(f'important params: {important_configs_dict}')
    return param, important_configs_dict


"""multithread + multiprocess"""


def _load_data_one_thread(folder_name, task_ind):
    result = {task_ind: None}
    try:
        _result = _get_parameter(folder_name)
        result[task_ind] = _result
    except Exception as e:
        import traceback
        Logger.local_log(f'[WARNING] unexpected Exception!!!! {e}')
        traceback.print_exc()
    return result


def _load_data_multi_thread(thread_num, path_list, task_ind_list, plot_config_dict):
    daemon_th = threading.Thread(target=_check_parent_alive, args=(os.getppid(),))
    daemon_th.daemon = True  # 设置为守护线程，确保主进程结束时该线程也会结束
    daemon_th.start()
    for k in plot_config_dict:
        setattr(plot_config, k, plot_config_dict[k])
    thread_num = min(thread_num, len(path_list))
    args = [path_list, task_ind_list]
    if thread_num == 1:
        result_dict = dict()
        for arg in zip(*args):
            for k, v in _load_data_one_thread(*arg).items():
                result_dict[k] = v
    else:
        thread_exe = ThreadPoolExecutor(max_workers=thread_num)
        result_dict = dict()
        for result_tmp in thread_exe.map(_load_data_one_thread, *args):
            for k, v in result_tmp.items():
                result_dict[k] = v

    return result_dict


def _load_data_multi_process(process_num, thread_num, path_list):
    process_num = min(process_num, len(path_list))
    process_num = max(process_num, 1)
    result_dict = dict()
    task_ind_list = [i for i in range(len(path_list))]
    path_array = []
    task_ind_array = []
    tasks_num_per_thread = len(path_list) // process_num
    start_ind = 0
    for i in range(process_num - 1):
        path_array.append(path_list[start_ind:start_ind + tasks_num_per_thread])
        task_ind_array.append(task_ind_list[start_ind:start_ind + tasks_num_per_thread])
        start_ind = start_ind + tasks_num_per_thread
    if start_ind < len(path_list):
        path_array.append(path_list[start_ind:])
        task_ind_array.append(task_ind_list[start_ind:])
    thread_num_list = [thread_num for _ in path_array]
    plot_config_dict = {k: getattr(plot_config, k) for k in plot_config.global_plot_configs()}
    plot_config_list = [plot_config_dict for _ in path_array]
    args = [thread_num_list, path_array, task_ind_array, plot_config_list]
    if process_num == 1:
        for item in zip(*args):
            result_tmp = _load_data_multi_thread(*item)
            for k, v in result_tmp.items():
                result_dict[k] = v
    else:
        process_exe = ProcessPoolExecutor(max_workers=process_num)
        for result_tmp in process_exe.map(_load_data_multi_thread, *args):
            for k, v in result_tmp.items():
                result_dict[k] = v

    results = []
    for i in range(len(path_list)):
        if i in result_dict:
            results.append(result_dict[i])
        else:
            results.append(None)
    return results


"""end_multithread + end_multiprocess"""


def get_parameter(folder_name):
    param, important_configs_dict = _get_parameter(folder_name)
    if param is None:
        return None, None, None, None, None, None, None
    dtree, full_path, name, filesize, filesize_bytes = generate_path_tree(folder_name)
    return param, dtree, full_path, name, filesize, filesize_bytes, important_configs_dict


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
        self.filesize_bytes = []

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

    @staticmethod
    def getfile_size_numeric(filename):
        fsize = os.path.getsize(filename)
        return fsize

    def generate_tree(self, n=0):
        if self.pathname.is_file():
            # file is able to downloads
            self.tree += '    |' * n + '-' * 4 + self.pathname.name + '\n'
            self.full_path += [str(self.pathname.relative_to(os.path.dirname(self.root_name)))]
            self.name.append(str(self.pathname.name))
            self.filesize.append(DirectionTree.getfile_size(str(self.pathname)))
            self.filesize_bytes.append(DirectionTree.getfile_size_numeric(str(self.pathname)))
        elif self.pathname.is_dir():
            self.full_path += [None]
            self.name.append(str(self.pathname.name))
            self.filesize.append(0)
            self.filesize_bytes.append(0)
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

    # Logger.local_log(dtree.tree)
    # Logger.local_log(dtree.full_path)
    return dtree.tree, dtree.full_path, dtree.name, dtree.filesize, dtree.filesize_bytes


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
        # Logger.local_log(f'{v} is classified to {config_type[k]}')
    return config_type


def get_record_data_item(folder_name):
    full_folder = os.path.join(plot_config.PLOT_LOG_PATH, folder_name)
    if 'progress.csv' not in os.listdir(full_folder):
        return [], 0, None
    data_path = os.path.join(full_folder, 'progress.csv')
    try:
        data = pd.read_csv(data_path)
        value_list = list(data.keys())
        if len(value_list) == 1:
            data = pd.read_table(data_path)
            value_list = list(data.keys())

        return value_list, len(data), data
    except Exception as e:
        Logger.local_log(f'read csv from {data_path} failed, because {e}')
    return [], 0, None


def config_to_short_name(config, data_merger, short_name_from_config, short_name_property):
    elements = []
    for k in data_merger:
        if k in config:
            elements.append(make_merger_feature(k, config[k]))
    short_name_origin = list_embedding(elements)
    short_name = merger_to_short_name(elements, short_name_from_config, short_name_property)
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
    if not len(config_new['DATA_IGNORE_PROPERTY']) == len(config_new['DATA_IGNORE']):
        print(f'DATA_IGNORE_PROPERTY does not valid, reinit it')
        config_new['DATA_IGNORE_PROPERTY'] = []
        for item in config_new['DATA_IGNORE']:
            config_new['DATA_IGNORE_PROPERTY'].append({k: {} for k in item})
        k_set_mismatch = True
    if not len(config_new['DATA_SELECT_PROPERTY']) == len(config_new['DATA_SELECT']):
        print(f'DATA_SELECT_PROPERTY does not valid, reinit it')
        config_new['DATA_SELECT_PROPERTY'] = []
        for item in config_new['DATA_SELECT']:
            config_new['DATA_SELECT_PROPERTY'].append({k: {} for k in item})
        k_set_mismatch = True
    if not len(config_new['SHORT_NAME_FROM_CONFIG_PROPERTY']) == len(config_new['SHORT_NAME_FROM_CONFIG']):
        config_new['SHORT_NAME_FROM_CONFIG_PROPERTY'] = dict()
        print(f'SHORT_NAME_FROM_CONFIG_PROPERTY does not valid, reinit it')
        for k in config_new['SHORT_NAME_FROM_CONFIG']:
            config_new['SHORT_NAME_FROM_CONFIG_PROPERTY'][k] = dict()
        k_set_mismatch = True
    if k_set_mismatch:
        save_config(config_new, config_name)


def can_ignore(config, data_ignore, data_merger, data_ignore_property):
    if len(data_ignore) == 0:
        return False
    if config is None:
        return True
    match_ignore = False
    short_name_origin, _ = config_to_short_name(config, data_merger, {}, {})
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
    short_name_origin, _ = config_to_short_name(config, data_merger, {}, {})
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
                       data_ignore_property=None, data_select_property=None,
                       data_short_name_property=None, user_data=None, use_cache=False):
    Logger.local_log(f'start listing experiment...')
    start_time = time.time()
    if user_data is None:
        use_cache = False
    if use_cache and user_data is not None and isinstance(user_data, dict):
        if 'all_folders' in user_data and isinstance(user_data['all_folders'], list) \
                and 'all_folders_data' in user_data and isinstance(user_data['all_folders_data'], list):
            pass
        else:
            use_cache = False
    if use_cache:
        all_folders = user_data['all_folders']
    else:
        all_folders = list_current_experiment()
        random.seed(1)
        random.shuffle(all_folders)
        if user_data is not None and isinstance(user_data, dict):
            user_data['all_folders'] = all_folders
    Logger.local_log(f'finish listing experiment, cost {time.time() - start_time}')
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
    Logger.local_log(f'start loading all configs...')
    start_time = time.time()
    if use_cache:
        all_folders_data = user_data['all_folders_data']
    else:
        all_folders_data = _load_data_multi_process(plot_config.PROCESS_NUM_LOAD_DATA, plot_config.THREAD_NUM, all_folders)
        if user_data is not None and isinstance(user_data, dict):
            user_data['all_folders_data'] = all_folders_data
    Logger.local_log(f'finish loading configs, cost {time.time() - start_time}')
    start_time = time.time()
    for folder_ind, (config, important_config) in enumerate(all_folders_data):
        folder = all_folders[folder_ind]
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
        short_name, short_name_nick = config_to_short_name(config, data_merge, data_short_name_dict,
                                                           data_short_name_property)
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
                elif isinstance(v, dict):
                    v = str(v)
                try:
                    _possible_config[k].add(v)
                except Exception as e:
                    import traceback
                    print(f'error: {e}')
                    traceback.print_exc()
        _selected_choices = dict()
        for k in _possible_config:
            _possible_config[k] = list(_possible_config[k])
        for k, v in _possible_config.items():
            if len(v) > 1:
                _selected_choices[k] = list(v)
        return _possible_config, _selected_choices

    possible_config, selected_choices = stat_config(config_list)
    possible_config_ignore, selected_choices_ignore = stat_config(config_list_ignore)
    Logger.local_log(f'short name to ind: {short_name_to_ind}')
    sorted_res = [*zip(*sorted([*zip(alg_idxs, folder_list, nick_name_list)], key=lambda x: x[0]))]
    sorted_res_ignore = [
        *zip(*sorted([*zip(alg_idxs_ignore, folder_ignore, nick_name_ignore_list)], key=lambda x: x[0]))]
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


def record_config_for_user(user, config_name):
    user_history_data_path = os.path.join(page_config.USER_DATA_PATH, f"{user}.json")
    have_user_history_data = os.path.exists(user_history_data_path)
    if have_user_history_data:
        try:
            user_data = json.load(open(user_history_data_path, 'r'))
            user_data['config'] = config_name
        except Exception as e:
            have_user_history_data = False
    if not have_user_history_data:
        print(user_history_data_path)
        os.makedirs(os.path.dirname(user_history_data_path), exist_ok=True)
        user_data = dict(config=config_name)

    safe_dump(user_data, user_history_data_path)

