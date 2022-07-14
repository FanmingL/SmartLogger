import sys
import os
import time

import smart_logger.common.plot_config as plot_config
from smart_logger.util_logger.logger import Logger
import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import random
import seaborn as sns
import matplotlib
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import json
import re
sns.set_theme()


line_style = [
    ['tab:red', '-', 'o'],
    ['tab:blue', '-', 'd'],
    ['tab:green', '-', 'v'],
    ['tab:orange', '-', '^'],
    ['tab:purple', '-', 's'],
    ['tab:brown', '-', 'H'],
    ['tab:gray', '-', '>'],
    ['tab:olive', '-', 'X'],
    ['tab:pink', '-', '1'],
    ['blue', '-', 'p'],
    ['green', '-', 'P'],
]

def title_tuple_to_str(title):
    try:
        title_idx = int(plot_config.TITLE_NAME_IDX)
    except ValueError as e:
        title_idx = None
    except TypeError as e:
        title_idx = None
    if len(title) == 0:
        return title[0]
    if title_idx is None:
        return ', '.join([*title])
    return title[title_idx]

def make_merger_feature(k, v):
    if isinstance(v, str):
        return v
    else:
        return f'{k}_{v}'

def list_embedding(str_list):
    return '+'.join(sorted([str(item) for item in str_list]))


def standardize_string(s):
    return list_embedding(s.split('+'))


def smooth(y, radius, mode='two_sided', valid_only=False):
    if len(y) < 2*radius+1:
        return np.ones_like(y) * y.mean()
    elif mode == 'two_sided':
        convkernel = np.ones(2 * radius+1)
        out = np.convolve(y, convkernel, mode='same') / np.convolve(np.ones_like(y), convkernel, mode='same')
        if valid_only:
            out[:radius] = out[-radius:] = np.nan
    elif mode == 'causal':
        convkernel = np.ones(radius)
        out = np.convolve(y, convkernel, mode='full') / np.convolve(np.ones_like(y), convkernel, mode='full')
        out = out[:-radius+1]
        if valid_only:
            out[:radius] = np.nan
    else:
        raise NotImplementedError(f'{mode} has not been implemented!')
    return out


def sort_algs(exist_algs, color_ind=None, alg_to_color_idx=None):
    if alg_to_color_idx is None:
        alg_to_color_idx = dict()
    if color_ind is None:
        color_ind = 0
    algs = [alg for alg in exist_algs]
    if len(plot_config.PLOTTING_ORDER) > 0:
        algs = [_alg for _alg in plot_config.PLOTTING_ORDER if _alg in exist_algs]
        for _alg in exist_algs:
            if _alg not in algs:
                algs.append(_alg)
        if plot_config.PRIMARY_ALG in algs:
            algs = [plot_config.PRIMARY_ALG] + [a for a in algs if not a == plot_config.PRIMARY_ALG]
        for ind, item in enumerate(plot_config.PLOTTING_ORDER):
            color_ind = ind
            if item in exist_algs and item not in alg_to_color_idx:
                alg_to_color_idx[item] = color_ind
            color_ind += 1
    else:
        algs = sorted(algs)
        if plot_config.PRIMARY_ALG in algs:
            algs = [plot_config.PRIMARY_ALG] + [a for a in algs if not a == plot_config.PRIMARY_ALG]

    return algs, color_ind, alg_to_color_idx


def stat_data(data):
    # data_mean = [0 for _ in data[0]]
    # data_error = [0 for _ in data[0]]
    data = np.array(data)
    data_mean = np.mean(data, axis=0)
    if data.shape[-1] > 1:
        data_std = np.std(data, axis=0)
    else:
        data_std = np.ones_like(data_mean) * 1e-9
    data_error = data_std / np.sqrt(data.shape[0])
    # for i in range(len(data_mean)):
    #     data_list = [item[i] for item in data]
    #     mean_val = np.mean(data_list)
    #     std = 1e-9 if len(data_list) == 1 else np.std(data_list)
    #     std_error = std / np.sqrt(len(data_list))
    #     data_mean[i] = mean_val
    #     data_error[i] = std_error
    return data_mean, data_error


def merger_to_short_name(merger, short_name_from_config):
    _res = list_embedding(merger)
    _res_standard = standardize_string(_res)

    short_name_config = dict()
    for k, v in short_name_from_config.items():
        short_name_config[standardize_string(k)] = v

    if _res_standard in short_name_config:
        _res = short_name_config[_res_standard]
    return _res


def _load_data(folder_name):
    try:
        progress_data = os.path.join(folder_name, 'progress.csv')
        parameter_data = os.path.join(folder_name, 'config', 'parameter.json')
        parameter_data_possible = os.path.join(folder_name, 'parameter.json')
        running_config_data = os.path.join(folder_name, 'config', 'running_config.json')
        param = dict()

        if os.path.exists(parameter_data):
            with open(parameter_data, 'r') as f:
                param1 = json.load(f)
            param.update(param1)
        if os.path.exists(parameter_data_possible):
            with open(parameter_data_possible, 'r') as f:
                param_possible = json.load(f)
            param.update(param_possible)
        if os.path.exists(running_config_data):
            with open(running_config_data, 'r') as f:
                param2 = json.load(f)
            param.update(param2)
        assert len(param) > 0, f"at least one parameter should exist!!!! {folder_name} {param}"
        data_merger_feature = []
        for merger in plot_config.DATA_MERGER:
            # assert merger in param, f"{merger} not in configs, it should be found!!"
            if merger in param:
                data_merger_feature.append(make_merger_feature(merger, param[merger]))
        match_ignore = False
        if plot_config.USE_IGNORE_RULE:
            for data_ignore in plot_config.DATA_IGNORE:
                match_ignore = True

                for k, v in data_ignore.items():
                    if k == '__SHORT_NAME__':
                        if not standardize_string(v) == standardize_string(list_embedding(data_merger_feature)):
                            match_ignore = False
                            break
                    elif k not in param or (isinstance(v, str) and re.match(v, param[k]) is None) \
                    or (not isinstance(v, str) and not v == param[k]):
                        match_ignore = False
                        break
                if match_ignore:
                    break
        else:
            match_select = False
            for data_select in plot_config.DATA_SELECT:
                match_select = True

                for k, v in data_select.items():
                    if k not in param or (isinstance(v, str) and re.match(v, param[k]) is None) \
                    or (not isinstance(v, str) and not v == param[k]):
                        match_select = False
                        break
                if match_select:
                    break
            if match_select:
                match_ignore = False
            else:
                match_ignore = True
        if match_ignore:
            return None
        data = pd.read_csv(progress_data)
        if len(data.keys()) == 1:
            data = pd.read_table(progress_data)
        for k, v in plot_config.DATA_KEY_RENAME_CONFIG.items():
            if k in data and v not in data:
                data[v] = data[k]
        Logger.local_log(f'[ {len(data)} ] data rows for {folder_name}: {len(data)}')
        data_str = data.select_dtypes(include=['object'])
        if len(list(data_str.keys())) > 0:
            Logger.local_log(f'invalid keys (not numerical value): {list(data_str.keys())}')
        data = data.dropna(how='all')
        separator_values = []
        for separator in plot_config.FIGURE_SEPARATION:
            assert separator in param, f"{separator} not in configs, it should be found!!"
            separator_value = param[separator]
            if isinstance(separator_value, str):
                separator_value = separator_value
            elif isinstance(separator_value, list):
                separator_value = list_embedding(separator_value)
            elif isinstance(separator_value, tuple):
                separator_value = list_embedding(list(separator_value))
            else:
                separator_value = str(separator_value)
            separator_values.append(separator_value)

        result = dict(separator=separator_values, merger=data_merger_feature, config_dict=param, data=data,
                      folder_name=os.path.basename(folder_name))
    except Exception as e:
        Logger.local_log('[WARNING] meeting an exception while reading: {}'.format(e))
        result = None
    return result


def _load_data_one_thread(folder_name, task_ind):
    result = {task_ind: None}
    try:
        _result = _load_data(folder_name)
        result[task_ind] = _result
    except Exception as e:
        import traceback
        Logger.local_log(f'[WARNING] unexpected Exception!!!! {e}')
        traceback.print_exc()
    return result


def _load_data_multi_thread(thread_num, path_list, task_ind_list, plot_config_dict):
    for k in plot_config_dict:
        setattr(plot_config, k, plot_config_dict[k])
    thread_num = min(thread_num, len(path_list))
    thread_exe = ThreadPoolExecutor(max_workers=thread_num)
    result_dict = dict()
    args = [path_list, task_ind_list]
    for result_tmp in thread_exe.map(_load_data_one_thread, *args):
        for k, v in result_tmp.items():
            result_dict[k] = v

    return result_dict


def _load_data_multi_process(process_num, thread_num, path_list):
    process_num = min(process_num, len(path_list))
    process_exe = ProcessPoolExecutor(max_workers=process_num)
    result_dict = dict()
    task_ind_list = [i for i in range(len(path_list))]
    path_array = []
    task_ind_array = []
    tasks_num_per_thread = len(path_list) // process_num
    start_ind = 0
    for i in range(process_num - 1):
        path_array.append(path_list[start_ind:start_ind+tasks_num_per_thread])
        task_ind_array.append(task_ind_list[start_ind:start_ind+tasks_num_per_thread])
        start_ind = start_ind + tasks_num_per_thread
    if start_ind < len(path_list):
        path_array.append(path_list[start_ind:])
        task_ind_array.append(task_ind_list[start_ind:])
    thread_num_list = [thread_num for _ in path_array]
    plot_config_dict = {k: getattr(plot_config, k) for k in plot_config.global_plot_configs()}
    plot_config_list = [plot_config_dict for _ in path_array]
    args = [thread_num_list, path_array, task_ind_array, plot_config_list]
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


def collect_data():
    """
    返回一个字典, 第一个key对应了FIGURE_SEPARATION[0]对应的属性的所有取值, 下一层对应了FIGURE_SEPARATION[1]的所有取值...
    倒数第二层字典包括了DATA_MERGER对应的所有值的可能组合
    最后一层是个list，里面包含若干字典，字典包括四个key, config_dict, data, separator, 和merger，config_dict对应了一个存放参数的字典，data对应了数据
    另外两个key描述其特征
    """
    data = dict()
    folder_list = []
    for root, _, files in os.walk(plot_config.PLOT_LOG_PATH, topdown=True):
        for name in files:
            if name == 'progress.csv':
                folder_list.append(root)
    total_raw_data = _load_data_multi_process(plot_config.PROCESS_NUM, plot_config.THREAD_NUM, folder_list)
    for root, raw_data in zip(folder_list, total_raw_data):
        Logger.local_log(f'try to load data from {root}')
        if raw_data is None:
            Logger.local_log(f'load data from {root} failed')
            continue
        separator = raw_data['separator']
        merger = raw_data['merger']
        figure_content = tuple(separator)
        alg_name = merger_to_short_name(merger, plot_config.SHORT_NAME_FROM_CONFIG)
        if figure_content not in data:
            data[figure_content] = dict()
        if alg_name not in data[figure_content]:
            data[figure_content][alg_name] = []
        data[figure_content][alg_name].append(raw_data)
    data_key_sorted = sorted([k for k in data], key=lambda x: x[0])
    data = {k: data[k] for k in data_key_sorted}
    for k, v in data.items():
        for k1, v1 in v.items():
            Logger.local_log(f'figure_content: {k}, algo_name: {k1}, data num: {len(v1)}')
    return data


def _remove_nan(x_data, y_data_list):
    y_data = np.array(y_data_list)
    y_data_mean = np.mean(y_data, axis=0)
    nan_mask = np.isnan(y_data_mean) | np.isnan(x_data)
    if np.any(nan_mask):
        y_data = y_data[:, ~nan_mask]
        x_data = x_data[~nan_mask]
        y_data_list = [item for item in y_data]
        return x_data, y_data_list
    else:
        return x_data, y_data_list


def _plot_sub_figure(data, fig_row, fig_column, figsize, alg_to_color_idx, x_name, y_name, plot_config_dict):
    Logger.local_log(f'PID: {os.getpid()} started!!')
    for k in plot_config_dict:
        setattr(plot_config, k, plot_config_dict[k])
    sub_figure_content = [k for k in data]
    sub_figure_content = sorted(sub_figure_content)
    fig_ind = 0
    alg_to_line_handler = dict()
    alg_to_seed_num = dict()
    f, axarr = plt.subplots(fig_row, fig_column, sharex=False, squeeze=False, figsize=figsize)
    plt.subplots_adjust(wspace=plot_config.SUBPLOT_WSPACE, hspace=plot_config.SUBPLOT_HSPACE)
    for sub_figure in sub_figure_content:
        _col = fig_ind % fig_column
        _row = fig_ind // fig_column
        ax = axarr[_row][_col]
        alg_count = 0
        algs, _, _ = sort_algs(data[sub_figure])
        if plot_config.PRIMARY_ALG in algs:
            algs = [plot_config.PRIMARY_ALG] + [a for a in algs if not a == plot_config.PRIMARY_ALG]
        for alg_name in algs:
            data_alg_list = data[sub_figure][alg_name]
            if alg_name not in alg_to_color_idx:
                continue
            have_y_name = True
            for item in data_alg_list:
                if y_name not in item['data']:
                    have_y_name = False
            if not have_y_name:
                if y_name in data_alg_list[0]['data']:
                    Logger.local_log(
                        f'path need to be check, alg_name: {alg_name}, {[item["folder_name"] for item in data_alg_list]}')
                continue
            if len(data_alg_list) == 0:
                Logger.local_log(f'{x_name}-{y_name} cannot be found in data-{sub_figure}-{alg_name}')
                continue
            x_data = [data_alg['data'][x_name] for data_alg in data_alg_list]
            y_data = [data_alg['data'][y_name] for data_alg in data_alg_list]
            data_len = [len(item) for item in x_data]
            min_data_len = min(data_len)
            seed_num = len(data_len)
            x_data = [np.array(data[:min_data_len:plot_config.PLOT_FOR_EVERY]) for data in x_data]
            y_data = [np.array(data[:min_data_len:plot_config.PLOT_FOR_EVERY]) for data in y_data]
            x_data = x_data[0]
            x_data, y_data = _remove_nan(x_data, y_data)
            if not str(plot_config.XMAX) == 'None':
                final_ind = np.argmin(np.square(np.array(x_data) - float(plot_config.XMAX))) + 1
                x_data = x_data[:final_ind]
                y_data = [data[:final_ind] for data in y_data]
            min_data_len = min_data_len // plot_config.PLOT_FOR_EVERY
            y_data, y_data_error = stat_data(y_data)
            if plot_config.USE_SMOOTH:
                y_data = smooth(y_data, radius=plot_config.SMOOTH_RADIUS)
            Logger.local_log(f'PID:{os.getpid()}, figure: {sub_figure}, alg: {alg_name}, data_len: {data_len}, min len: {min(data_len)}, {min_data_len}')
            color_idx, type_idx, marker_idx = alg_to_color_idx[alg_name]
            line_color = line_style[color_idx][0]
            line_type = line_style[type_idx][1]
            marker = line_style[marker_idx][2]

            curve, = ax.plot(x_data, y_data, color=line_color,
                             linestyle=line_type, marker=marker, label=alg_name,
                             linewidth=plot_config.LINE_WIDTH, markersize=plot_config.MARKER_SIZE,
                             markevery=max(min_data_len // 8, 1))
            if alg_name not in alg_to_line_handler:
                alg_to_line_handler[alg_name] = curve
                alg_to_seed_num[alg_name] = seed_num
            if len(data_len) > 1:
                ax.fill_between(x_data, y_data - y_data_error, y_data + y_data_error, color=line_color,
                                alpha=plot_config.SHADING_ALPHA)
            if _col == 0:
                if str(plot_config.FIXED_Y_LABEL) == 'None':
                    ax.set_ylabel(y_name, fontsize=plot_config.FONTSIZE_LABEL)
                else:
                    ax.set_ylabel(plot_config.FIXED_Y_LABEL, fontsize=plot_config.FONTSIZE_LABEL)
            ax.set_xlabel(x_name, fontsize=plot_config.FONTSIZE_LABEL)
            ax.tick_params(axis='x', labelsize=plot_config.FONTSIZE_XTICK)
            ax.tick_params(axis='y', labelsize=plot_config.FONTSIZE_YTICK)
            ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))

            if plot_config.X_AXIS_SCI_FORM:
                ax.ticklabel_format(style='sci', scilimits=(-1, 2), axis='x')
                ax.xaxis.offsetText.set_fontsize(plot_config.FONTSIZE_YTICK)
            title_name = title_tuple_to_str(sub_figure)
            if not plot_config.TITLE_SUFFIX == 'None':
                title_name = f'{title_name}{plot_config.TITLE_SUFFIX}'
            ax.set_title(title_name, fontsize=plot_config.FONTSIZE_TITLE)
            ax.grid(True)
            alg_count += 1
            if plot_config.XMAX is not None and not str(plot_config.XMAX) == 'None':
                ax.set_xlim(right=int(plot_config.XMAX))
        if alg_count == 0:
            ax.set_title(sub_figure, fontsize=plot_config.FONTSIZE_TITLE)

        fig_ind += 1
    names = [k for k in alg_to_line_handler]
    if len(plot_config.LEGEND_ORDER) > 0:
        ordered_names = [k for k in plot_config.LEGEND_ORDER if k in names]
        remain_names = [k for k in names if k not in ordered_names]
        names = ordered_names + remain_names
    curves = [alg_to_line_handler[k] for k in names]
    final_names = []
    for ind, name in enumerate(names):
        if str(plot_config.SHOW_SEED_NUM) == 'True':
            final_names.append(name + f' ({alg_to_seed_num[name]})')
        else:
            final_names.append(name)
    axarr[0][0].legend(handles=curves, labels=final_names, loc='center left', bbox_to_anchor=(plot_config.LEGEND_POSITION_X, plot_config.LEGEND_POSITION_Y),
                       ncol=plot_config.LEGEND_COLUMN, fontsize=plot_config.FONTSIZE_LEGEND, frameon=plot_config.USE_LEGEND_FRAME)
    sup_title_name = y_name
    if plot_config.RECORD_DATE_TIME:
        sup_title_name += ': {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if plot_config.NEED_SUP_TITLE:
        plt.suptitle(sup_title_name, fontsize=plot_config.FONTSIZE_SUPTITLE, y=plot_config.SUPTITLE_Y)
    saving_name = y_name
    if not plot_config.OUTPUT_FILE_PREFIX == 'None':
        saving_name = plot_config.OUTPUT_FILE_PREFIX + saving_name
    os.makedirs(plot_config.PLOT_FIGURE_SAVING_PATH, exist_ok=True)
    png_saving_path = os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, f'{saving_name}.png')
    pdf_saving_path = os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, f'{saving_name}.pdf')
    os.makedirs(os.path.dirname(png_saving_path), exist_ok=True)
    Logger.local_log(f'saving PDF to file://{pdf_saving_path}')
    Logger.local_log(f'saving PNG to file://{png_saving_path}')
    f.savefig(png_saving_path, bbox_inches='tight', dpi=plot_config.PNG_DPI)
    f.savefig(pdf_saving_path, bbox_inches='tight')
    return png_saving_path, x_name, y_name


def _make_subtable(data, x_name, y_name, at_x, plot_config_dict, iter, alg_as_row_header):
    for k in plot_config_dict:
        setattr(plot_config, k, plot_config_dict[k])
    sub_figure_content = [k for k in data]
    sub_figure_content = sorted(sub_figure_content)
    fig_ind = 0
    summary_dict = dict()
    for sub_figure in sub_figure_content:
        algs, _, _ = sort_algs(data[sub_figure])
        for alg_name in algs:
            data_alg_list = data[sub_figure][alg_name]
            have_y_name = True
            for item in data_alg_list:
                if y_name not in item['data']:
                    have_y_name = False
            if not have_y_name:
                if y_name in data_alg_list[0]['data']:
                    Logger.local_log(
                        f'path need to be check, alg_name: {alg_name}, {[item["folder_name"] for item in data_alg_list]}')
                continue
            x_data = [data_alg['data'][x_name] for data_alg in data_alg_list]
            y_data = [data_alg['data'][y_name] for data_alg in data_alg_list]
            data_len = [len(item) for item in x_data]
            min_data_len = min(data_len)
            x_data = [np.array(data[:min_data_len]) for data in x_data]
            y_data = [np.array(data[:min_data_len]) for data in y_data]
            x_data = x_data[0]
            x_data, y_data = _remove_nan(x_data, y_data)
            if not str(plot_config.XMAX) == 'None':
                final_ind = np.argmin(np.square(np.array(x_data) - float(plot_config.XMAX))) + 1
                x_data = x_data[:final_ind]
                y_data = [data[:final_ind] for data in y_data]

            y_data, y_data_error = stat_data(y_data)
            y_data_error = np.array(y_data_error)
            if plot_config.USE_SMOOTH:
                y_data = smooth(y_data, radius=plot_config.SMOOTH_RADIUS)
            if at_x is not None:
                idx = np.argmin(np.square(x_data.astype(np.float) - at_x))
                selected_mean = y_data[idx]
                selected_error = y_data_error[idx]
            elif iter is not None:
                selected_mean = y_data[iter]
                selected_error = y_data_error[iter]
            else:
                selected_mean = y_data[-1]
                selected_error = y_data_error[-1]
            if len(data_len) <= 1:
                selected_error = 0
            if sub_figure not in summary_dict:
                summary_dict[sub_figure] = dict()
            summary_dict[sub_figure][alg_name] = (selected_mean, selected_error)
            Logger.local_log(f'table: {sub_figure}, alg: {alg_name}, x-y: {x_name}-{y_name}, data_len: {data_len}, min len: {min(data_len)}, selected mean: {selected_mean}, selected error: {selected_error}')

        fig_ind += 1
    if alg_as_row_header:
        summary_dict_transpose = dict()
        for k1 in summary_dict:
            for k2 in summary_dict[k1]:
                if k2 not in summary_dict_transpose:
                    summary_dict_transpose[k2] = dict()
                summary_dict_transpose[k2][k1] = summary_dict[k1][k2]
        summary_dict = summary_dict_transpose
    return summary_dict, x_name, y_name


def _plotting(data):
    sub_figure_content = [k for k in data]
    sub_figure_content = sorted(sub_figure_content, key=lambda x: x[0])
    Logger.local_log(f'total sub-figures: {sub_figure_content}')
    fig_row = int(np.ceil(len(sub_figure_content) / plot_config.MAX_COLUMN))
    fig_column = min(plot_config.MAX_COLUMN, len(sub_figure_content))
    fig_row = max(fig_row, 1)
    fig_column = max(fig_column, 1)
    figsize = (plot_config.SUBFIGURE_WIDTH * fig_column, plot_config.SUBFIGURE_HEIGHT * fig_row)
    Logger.local_log(f'making figure {fig_row} row {fig_column} col, size: {figsize}')
    random.seed(1)
    total_f = []
    total_png = []
    alg_to_color_idx = dict()
    used_color = set()
    color_ind = 0
    for x_name, y_name in plot_config.PLOTTING_XY:
        for sub_figure in sub_figure_content:
            algs, color_ind, alg_to_color_idx = sort_algs(data[sub_figure], color_ind, alg_to_color_idx)
            for alg_name in algs:
                data_alg_list = data[sub_figure][alg_name]
                have_y_name = True
                for item in data_alg_list:
                    if y_name not in item['data']:
                        have_y_name = False
                if not have_y_name:
                    if y_name in data_alg_list[0]['data']:
                        Logger.local_log(f'path need to be check, alg_name: {alg_name}, {[item["folder_name"] for item in data_alg_list]}')
                    continue
                if alg_name not in alg_to_color_idx:
                    alg_idx = color_ind
                    color_ind += 1
                    alg_to_color_idx[alg_name] = alg_idx
                if not isinstance(alg_to_color_idx[alg_name], tuple):
                    style_num = len(line_style)
                    if alg_to_color_idx[alg_name] < style_num:
                        alg_idx = alg_to_color_idx[alg_name]
                        alg_to_color_idx[alg_name] = (alg_idx, alg_idx, alg_idx)
                    else:
                        for _ in range(100):
                            candidate = (
                                random.randint(0, style_num - 1), random.randint(0, style_num - 1),
                                random.randint(0, style_num - 1))
                            alg_to_color_idx[alg_name] = candidate
                            if candidate not in used_color:
                                break
                    used_color.add(alg_to_color_idx[alg_name])
    plotting_executor = ProcessPoolExecutor(max_workers=plot_config.PROCESS_NUM)
    futures = []
    for x_name, y_name in plot_config.PLOTTING_XY:
        plot_config_dict = {k: getattr(plot_config, k) for k in plot_config.global_plot_configs()}
        data_it = {}
        for k1 in data:
            for k2 in data[k1]:
                data_array = data[k1][k2]
                if k1 not in data_it:
                    data_it[k1] = {}
                if k2 not in data_it[k1]:
                    data_it[k1][k2] = []
                for _data in data_array:
                    if x_name in _data['data'] and y_name in _data['data']:
                        data_candidate = {}
                        for k in _data:
                            if k == 'data':
                                data_candidate['data'] = _data['data'][[x_name, y_name]]
                            else:
                                data_candidate[k] = _data[k]
                        data_it[k1][k2].append(data_candidate)
        futures.append(plotting_executor.submit(_plot_sub_figure, data_it, fig_row,
                                                fig_column, figsize, alg_to_color_idx, x_name, y_name, plot_config_dict))
    config_to_png_path = dict()
    for future in as_completed(futures):
        png_path, x_name, y_name = future.result()
        config_to_png_path[x_name+y_name] = png_path
    for x_name, y_name in plot_config.PLOTTING_XY:
        total_png.append(config_to_png_path[x_name+y_name])
    # 汇总图
    # pdf = matplotlib.backends.backend_pdf.PdfPages(os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, f'total_curve.pdf'))
    # for f in total_f:
    #     pdf.savefig(f, bbox_inches='tight')
    # pdf.close()
    # 汇总png
    # merge png
    Logger.local_log(f'start to merge PNG')
    png_images = []
    start_merge_time = time.time()
    from PIL import Image
    for png_file in total_png:
        Logger.local_log('load image from {}'.format(png_file))
        png_images.append(Image.open(png_file))
    cols = [image.size[0] for image in png_images]
    rows = [image.size[1] for image in png_images]
    max_col = max(cols)
    merge_png = Image.new('RGB', (max_col, sum(rows)), (255, 255, 255))
    for ind, png_file in enumerate(png_images):
        start_row = sum(rows[:ind])
        merge_png.paste(png_file, (0, start_row))
    total_png_output_path = os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, f"{plot_config.FINAL_OUTPUT_NAME}.png")
    merge_png.save(total_png_output_path, "PNG")
    Logger.local_log(f'saved png to {total_png_output_path} cost: {time.time() - start_merge_time}')


def _to_table(data, atx, iter, privileged_col_idx=None, placeholder=None, md=True):
    sub_figure_content = [k for k in data]
    sub_figure_content = sorted(sub_figure_content, key=lambda x: x[0])
    Logger.local_log(f'total sub-figures: {sub_figure_content}')
    fig_row = int(np.ceil(len(sub_figure_content) / plot_config.MAX_COLUMN))
    fig_column = min(plot_config.MAX_COLUMN, len(sub_figure_content))
    fig_row = max(fig_row, 1)
    fig_column = max(fig_column, 1)
    figsize = (plot_config.SUBFIGURE_WIDTH * fig_column, plot_config.SUBFIGURE_HEIGHT * fig_row)
    Logger.local_log(f'making figure {fig_row} row {fig_column} col, size: {figsize}')
    random.seed(1)
    for x_name, y_name in plot_config.PLOTTING_XY:
        for sub_figure in sub_figure_content:
            algs, _, _ = sort_algs(data[sub_figure])
            for alg_name in algs:
                data_alg_list = data[sub_figure][alg_name]
                have_y_name = True
                for item in data_alg_list:
                    if y_name not in item['data']:
                        have_y_name = False
                if not have_y_name:
                    if y_name in data_alg_list[0]['data']:
                        Logger.local_log(
                            f'path need to be check, alg_name: {alg_name}, {[item["folder_name"] for item in data_alg_list]}')
                    continue
    plotting_executor = ProcessPoolExecutor(max_workers=plot_config.PROCESS_NUM)
    futures = []
    alg_as_row_header = False
    for x_name, y_name in plot_config.PLOTTING_XY:
        plot_config_dict = {k: getattr(plot_config, k) for k in plot_config.global_plot_configs()}
        futures.append(plotting_executor.submit(_make_subtable, data, x_name, y_name, atx, plot_config_dict, iter, alg_as_row_header))
    summary_dict_buffer = dict()
    for future in as_completed(futures):
        summary_dict, x_name, y_name = future.result()
        summary_dict_buffer[y_name] = summary_dict
    if md:
        result_editor = summary_buffer_to_output_md(summary_dict_buffer, privileged_col_idx, placeholder, alg_as_row_header)
    else:
        result_editor = summary_buffer_to_output(summary_dict_buffer, privileged_col_idx, placeholder, alg_as_row_header)
    result = summary_buffer_to_output_html(summary_dict_buffer, privileged_col_idx, placeholder, alg_as_row_header)
    return result, result_editor


def standardize_row_and_col(item_name, row_header, alg_as_row_header):
    # row_header：是否是行首
    if row_header:
        if alg_as_row_header:
            # alg_name, str
            return item_name.replace('_', '-')
        else:
            return str(title_tuple_to_str(item_name)).replace('_', '-')
    else:
        if alg_as_row_header:
            # env_name, tuple
            return str(title_tuple_to_str(item_name)).replace('_', '-')
        else:
            # alg_name, str
            return item_name.replace('_', '-')


def summary_buffer_to_output(summary_dict_buffer, privileged_col_idx=None, placeholder=None, alg_as_row_header=False):
    final_str = ''
    for table_name in summary_dict_buffer:
        final_str = final_str + '\n\n' + '='*15 + f'Table: {table_name}' + '='*15 + '\n'
        summary_dict = summary_dict_buffer[table_name]
        row_id_list = [k for k in summary_dict.keys()]
        row_id_list = sorted(row_id_list)
        cols_keys = set()
        for row_name in row_id_list:
            row_content = summary_dict[row_name]
            for k in row_content:
                cols_keys.add(k)
        cols_keys = list(cols_keys)
        cols_keys = sorted(cols_keys)
        prid_cols_keys = []
        if privileged_col_idx is not None:
            prid_cols_keys = sorted([(k, v) for k, v in privileged_col_idx.items()], key=lambda x:x[1])
            prid_cols_keys = [item[0] for item in prid_cols_keys if item[0] in cols_keys]
        for item in cols_keys:
            if item not in prid_cols_keys:
                prid_cols_keys.append(item)
        task_list = prid_cols_keys
        task_list, _, _ = sort_algs(task_list)
        final_str = final_str + '{l|'
        for i in range(len(task_list)):
            final_str = final_str + 'r@{~$\\pm$~}l'
        final_str = final_str + '}\\toprule' + '\n' + '& '

        for ind, task in enumerate(task_list):
            final_str = final_str + '\\multicolumn{2}{c}{'
            task_safe = standardize_row_and_col(item_name=task, row_header=False, alg_as_row_header=alg_as_row_header)
            final_str = final_str + str(task_safe) + '}'
            if ind < len(task_list) - 1:
                final_str += ' & '
        final_str = final_str + '\\\\\\midrule' + '\n'
        valid_bit = 2
        for row_name in row_id_list:
            row_content = summary_dict[row_name]
            max_performance_ind, max_performance = 0, -10000000
            if not plot_config.TABLE_BOLD_MAX:
                max_performance = -max_performance
            final_str = final_str + standardize_row_and_col(item_name=row_name, row_header=True, alg_as_row_header=alg_as_row_header) + ' & '
            for ind_task, task in enumerate(task_list):
                if task in row_content:
                    data_mean, data_error = row_content[task]
                    if plot_config.TABLE_BOLD_MAX:
                        if data_mean > max_performance:
                            max_performance = data_mean
                            max_performance_ind = ind_task
                    else:
                        if data_mean < max_performance:
                            max_performance = data_mean
                            max_performance_ind = ind_task
            for ind_task, task in enumerate(task_list):

                if task in row_content:
                    data_mean, data_error = row_content[task]
                else:
                    data_mean, data_error = 0, 0

                if max_performance_ind == ind_task:
                    final_str = final_str + '$ \\mathbf{' + f"{round(data_mean, valid_bit)}" + '} $ & ' + '$ \\mathbf{' + f"{round(data_error, valid_bit)}" + '} $'
                else:
                    final_str = final_str + f"${round(data_mean, valid_bit)}$" + '& ' + f"${round(data_error, valid_bit)}$"

                if ind_task < len(task_list) - 1:
                    final_str = final_str + ' & '

            final_str = final_str + '\\\\' + '\n'
        final_str = final_str + '\\bottomrule' + '\n'
        final_str = final_str + '='*15 + f'End Table: {table_name}' + '='*15 + '\n'
    Logger.local_log(final_str)
    return final_str



def summary_buffer_to_output_md(summary_dict_buffer, privileged_col_idx=None, placeholder=None, alg_as_row_header=False):
    final_str = ''
    for table_name in summary_dict_buffer:
        final_str = final_str + '## ' + f'Table: {table_name}' + '\n'
        summary_dict = summary_dict_buffer[table_name]
        row_id_list = [k for k in summary_dict.keys()]
        row_id_list = sorted(row_id_list)
        cols_keys = set()
        for row_name in row_id_list:
            row_content = summary_dict[row_name]
            for k in row_content:
                cols_keys.add(k)
        cols_keys = list(cols_keys)
        cols_keys = sorted(cols_keys)
        prid_cols_keys = []
        if privileged_col_idx is not None:
            prid_cols_keys = sorted([(k, v) for k, v in privileged_col_idx.items()], key=lambda x:x[1])
            prid_cols_keys = [item[0] for item in prid_cols_keys if item[0] in cols_keys]

        for item in cols_keys:
            if item not in prid_cols_keys:
                prid_cols_keys.append(item)
        if placeholder is not None:
            placeholder_keys = sorted([(k, v) for k, v in placeholder.items()], key=lambda x: x[1])
            placeholder_keys = [item[0] for item in placeholder_keys if item[0] not in cols_keys]
            prid_cols_keys = prid_cols_keys + placeholder_keys
        task_list = prid_cols_keys
        task_list, _, _ = sort_algs(task_list)
        final_str = final_str + '||'
        for ind, task in enumerate(task_list):
            task_safe = standardize_row_and_col(task, row_header=False, alg_as_row_header=alg_as_row_header)
            final_str = final_str + task_safe + '|'
        final_str += '\n'
        length_placeholder = '-' * 6
        final_str = final_str + f'|:{length_placeholder}|'
        for ind, task in enumerate(task_list):
            final_str = final_str + f':{length_placeholder}:|'
        final_str += '\n'
        valid_bit = 2
        for row_name in row_id_list:
            row_content = summary_dict[row_name]
            max_performance_ind, max_performance = 0, -10000000
            if not plot_config.TABLE_BOLD_MAX:
                max_performance = -max_performance
            final_str = final_str + '|' + standardize_row_and_col(row_name, row_header=True, alg_as_row_header=alg_as_row_header) + ' | '
            for ind_task, task in enumerate(task_list):
                if task in row_content:
                    data_mean, data_error = row_content[task]
                    if plot_config.TABLE_BOLD_MAX:
                        if data_mean > max_performance:
                            max_performance = data_mean
                            max_performance_ind = ind_task
                    else:
                        if data_mean < max_performance:
                            max_performance = data_mean
                            max_performance_ind = ind_task
            for ind_task, task in enumerate(task_list):

                if task in row_content:
                    data_mean, data_error = row_content[task]
                else:
                    data_mean, data_error = 0, 0

                if max_performance_ind == ind_task:
                    final_str = final_str + '$ \\mathbf{'
                    final_str = final_str + f"{round(data_mean, valid_bit)}"
                    final_str = final_str + '} \\pm'
                    final_str = final_str + '\\mathbf{'
                    final_str = final_str + f"{round(data_error, valid_bit)}"
                    final_str = final_str + '} ^\star$'
                else:
                    final_str = final_str + f"${round(data_mean, valid_bit)}"
                    final_str = final_str + '\\pm '
                    final_str = final_str + f"{round(data_error, valid_bit)}$"
                final_str = final_str + ' | '
            final_str = final_str + '\n'
        final_str = final_str + '\n'

    Logger.local_log(final_str)
    return final_str


def summary_buffer_to_output_html(summary_dict_buffer, privileged_col_idx=None, placeholder=None, alg_as_row_header=False):
    final_str = ''
    for table_name in summary_dict_buffer:
        final_str = final_str + '<h3> ' + f'Table: {table_name}' + '</h3>' + '\n'
        final_str = final_str + '<table border="1" align="center" frame="hsides" rules="rows">'
        summary_dict = summary_dict_buffer[table_name]
        row_id_list = [k for k in summary_dict.keys()]
        row_id_list = sorted(row_id_list)
        cols_keys = set()
        for row_name in row_id_list:
            row_content = summary_dict[row_name]
            for k in row_content:
                cols_keys.add(k)
        cols_keys = list(cols_keys)
        cols_keys = sorted(cols_keys)
        prid_cols_keys = []
        if privileged_col_idx is not None:
            prid_cols_keys = sorted([(k, v) for k, v in privileged_col_idx.items()], key=lambda x:x[1])
            prid_cols_keys = [item[0] for item in prid_cols_keys if item[0] in cols_keys]

        for item in cols_keys:
            if item not in prid_cols_keys:
                prid_cols_keys.append(item)
        if placeholder is not None:
            placeholder_keys = sorted([(k, v) for k, v in placeholder.items()], key=lambda x: x[1])
            placeholder_keys = [item[0] for item in placeholder_keys if item[0] not in cols_keys]
            prid_cols_keys = prid_cols_keys + placeholder_keys
        task_list = prid_cols_keys
        task_list, _, _ = sort_algs(task_list)
        final_str = final_str + '<tr>\n'
        final_str = final_str + '<td>&nbsp;</td>\n'
        for ind, task in enumerate(task_list):
            task_safe = standardize_row_and_col(task, row_header=False, alg_as_row_header=alg_as_row_header)
            final_str = final_str + '<th>' + '{}'.format(task_safe) + '</th>\n'
        final_str += '</tr>\n'
        valid_bit = 2
        for row_name in row_id_list:
            row_content = summary_dict[row_name]
            max_performance_ind, max_performance = 0, -10000000
            if not plot_config.TABLE_BOLD_MAX:
                max_performance = -max_performance
            final_str = final_str + '<tr>'
            final_str = final_str + '<td style="text-align: left;">' + standardize_row_and_col(row_name, row_header=True, alg_as_row_header=alg_as_row_header) + '</td>\n'
            for ind_task, task in enumerate(task_list):
                if task in row_content:
                    data_mean, data_error = row_content[task]
                    if plot_config.TABLE_BOLD_MAX:
                        if data_mean > max_performance:
                            max_performance = data_mean
                            max_performance_ind = ind_task
                    else:
                        if data_mean < max_performance:
                            max_performance = data_mean
                            max_performance_ind = ind_task
            for ind_task, task in enumerate(task_list):
                final_str = final_str + '<td>'
                if task in row_content:
                    data_mean, data_error = row_content[task]
                else:
                    data_mean, data_error = 0, 0

                if max_performance_ind == ind_task:

                    final_str = final_str + '$ \\mathbf{'
                    final_str = final_str + f"{round(data_mean, valid_bit)}"
                    final_str = final_str + '} \\pm'
                    final_str = final_str + '\\mathbf{'
                    final_str = final_str + f"{round(data_error, valid_bit)}"
                    final_str = final_str + '} ^\star$'
                else:
                    final_str = final_str + f"${round(data_mean, valid_bit)}"
                    final_str = final_str + '\\pm '
                    final_str = final_str + f"{round(data_error, valid_bit)}$"
                final_str = final_str + ' </td> \n'
            final_str = final_str + ' </tr> \n'
        final_str = final_str + '</table>'
    Logger.local_log(final_str)
    return final_str

def _overwrite_config(config):
    for k in plot_config.global_plot_configs():
        if k in config:
            if not config[k] == getattr(plot_config, k):
                Logger.local_log(f'config {k} in file is {config[k]}, '
                      f'which is {getattr(plot_config, k)} in code, overwrite it!')
                setattr(plot_config, k, config[k])


def overwrite_config(config_json_path):
    if config_json_path is not None:
        if os.path.exists(config_json_path):
            with open(config_json_path, 'r') as f:
                config = json.load(f)
                _overwrite_config(config)
        else:
            Logger.local_log(f'{config_json_path} not exists! load failed!')


def plot(config_json_path=None):
    overwrite_config(config_json_path)
    data = collect_data()
    _plotting(data)

def _make_table(latex=None):
    data = collect_data()
    privileged_col_idx = dict(
    )
    placeholder = dict(
    )
    xmax = float(plot_config.XMAX) if not str(plot_config.XMAX) == 'None' else None
    result, result_source = _to_table(data, xmax, None, privileged_col_idx, placeholder=placeholder, md=False if latex else True)
    if latex is None:
        return result
    else:
        return result_source

def make_table(config_json_path=None):
    overwrite_config(config_json_path)
    return _make_table()

if __name__ == '__main__':
    # make_table('/Users/fanmingluo/Desktop/small_logger_cache/WEB_ROM/configs/formal_ablation_eta')
    make_table('/Users/fanmingluo/Desktop/small_logger_cache/WEB_ROM/configs/formal_consistency_table')
