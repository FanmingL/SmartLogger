import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# from smart_logger.common.plot_config import PLOT_LOG_PATH, PLOT_FIGURE_SAVING_PATH
# from smart_logger.common.plot_config import PLOTTING_XY, FIGURE_SEPARATION, DATA_MERGER, DATA_IGNORE, MAX_COLUMN
# from smart_logger.common.plot_config import USE_SMOOTH, SMOOTH_RADIUS, LEGEND_COLUMN, RECORD_DATE_TIME, X_AXIS_SCI_FORM
# from smart_logger.common.plot_config import SHORT_NAME_FROM_CONFIG, SUBPLOT_WSPACE, SUBPLOT_HSPACE, LEGEND_POSITION
import smart_logger.common.plot_config as plot_config
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
sns.set_theme()
# 绘图相关
# # 在绘图的时候，从哪里加载数据绘制
# PLOT_LOG_PATH = f"/home/luofm/Data/{LOG_DIR_BACKING_NAME}"
# # 绘图之后，将输出的图像文件存到哪里
# PLOT_FIGURE_SAVING_PATH = f"/home/luofm/Data/{LOG_DIR_BACKING_NAME}_figure"
# # 绘图时，忽略哪些日志文件
# PLOTTING_IGNORE_HEAD = []
# # 绘图时，X-Y轴数据
# PLOTTING_XY = [['timestep', 'EpRetTrain'], ['timestep', 'EpRetTest']]
# # 不同图片之间的数据，按照FIGURE_SEPARATION分开
# FIGURE_SEPARATION = ['env_name']
# # DATA_MERGER中所包含的量的值都一样的，看成是同一种数据
# DATA_MERGER = ['SHORT_NAME_SUFFIX', "information", "learn_embedding"]
# # 数据过滤规则
# DATA_IGNORE = [
#     {'information': "test_speed"}
# ]

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


def stat_data(data):
    data_mean = [0 for _ in data[0]]
    data_error = [0 for _ in data[0]]
    for i in range(len(data_mean)):
        data_list = [item[i] for item in data]
        mean_val = np.mean(data_list)
        std = 1e-9 if len(data_list) == 1 else np.std(data_list)
        std_error = std / np.sqrt(len(data_list))
        data_mean[i] = mean_val
        data_error[i] = std_error
    return data_mean, data_error


def merger_to_short_name(merger, short_name_from_config):
    _res = list_embedding(merger)
    short_name_config = dict()
    for k, v in short_name_from_config.items():
        short_name_config[standardize_string(k)] = v
    if _res in short_name_config:
        _res = short_name_config[_res]
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
        assert len(param) > 0, "at least one parameter should exist!!!!"
        data_merger_feature = []
        for merger in plot_config.DATA_MERGER:
            # assert merger in param, f"{merger} not in configs, it should be found!!"
            if merger in param:
                data_merger_feature.append(param[merger])
        match_ignore = False
        for data_ignore in plot_config.DATA_IGNORE:
            match_ignore = True
            for k, v in data_ignore.items():
                if k == '__SHORT_NAME__':
                    if not standardize_string(v) == standardize_string(list_embedding(data_merger_feature)):
                        match_ignore = False
                        break
                elif k not in param or not param[k] == v:
                    match_ignore = False
                    break
            if match_ignore:
                break
        if match_ignore:
            return None
        data = pd.read_csv(progress_data)
        if len(data.keys()) == 1:
            data = pd.read_table(progress_data)
        for k, v in plot_config.DATA_KEY_RENAME_CONFIG.items():
            if k in data and v not in data:
                data[v] = data[k]
        print(f'[ {len(data)} ] data rows for {folder_name}: {len(data)}')
        data_str = data.select_dtypes(include=['object'])
        if len(list(data_str.keys())) > 0:
            print(f'invalid keys (not numerical value): {list(data_str.keys())}')
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
        print('[WARNING] meeting an exception while reading: {}'.format(e))
        result = None
    return result


def collect_data():
    """
    返回一个字典, 第一个key对应了FIGURE_SEPARATION[0]对应的属性的所有取值, 下一层对应了FIGURE_SEPARATION[1]的所有取值...
    倒数第二层字典包括了DATA_MERGER对应的所有值的可能组合
    最后一层是个list，里面包含若干字典，字典包括四个key, config_dict, data, separator, 和merger，config_dict对应了一个存放参数的字典，data对应了数据
    另外两个key描述其特征
    """
    data = dict()
    for root, _, files in os.walk(plot_config.PLOT_LOG_PATH, topdown=True):
        for name in files:
            if name == 'progress.csv':
                print(f'try to load data from {root}')
                raw_data = _load_data(root)
                if raw_data is None:
                    print(f'load data from {root} failed')
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
            print(f'figure_content: {k}, algo_name: {k1}, data num: {len(v1)}')
    return data


def _plot_sub_figure(data, fig_row, fig_column, figsize, alg_to_color_idx, x_name, y_name, plot_config_dict):
    for k in plot_config_dict:
        setattr(plot_config, k, plot_config_dict[k])
    sub_figure_content = [k for k in data]
    sub_figure_content = sorted(sub_figure_content)
    fig_ind = 0
    alg_to_line_handler = dict()
    f, axarr = plt.subplots(fig_row, fig_column, sharex=False, squeeze=False, figsize=figsize)
    plt.subplots_adjust(wspace=plot_config.SUBPLOT_WSPACE, hspace=plot_config.SUBPLOT_HSPACE)
    for sub_figure in sub_figure_content:
        _col = fig_ind % fig_column
        _row = fig_ind // fig_column
        ax = axarr[_row][_col]
        alg_count = 0
        algs = [_alg for _alg in data[sub_figure]]
        algs = sorted(algs)
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
                    print(
                        f'path need to be check, alg_name: {alg_name}, {[item["folder_name"] for item in data_alg_list]}')
                continue
            x_data = [data_alg['data'][x_name] for data_alg in data_alg_list]
            y_data = [data_alg['data'][y_name] for data_alg in data_alg_list]
            data_len = [len(item) for item in x_data]
            min_data_len = min(data_len)
            x_data = [list(data)[:min_data_len] for data in x_data]
            y_data = [list(data)[:min_data_len] for data in y_data]
            x_data = x_data[0]
            y_data, y_data_error = stat_data(y_data)
            y_data = np.array(y_data)
            y_data_error = np.array(y_data_error)
            x_data = np.array(x_data)
            if plot_config.USE_SMOOTH:
                y_data = smooth(y_data, radius=plot_config.SMOOTH_RADIUS)
            print(f'figure: {sub_figure}, alg: {alg_name}, data_len: {data_len}, min len: {min(data_len)}')
            color_idx, type_idx, marker_idx = alg_to_color_idx[alg_name]
            line_color = line_style[color_idx][0]
            line_type = line_style[type_idx][1]
            marker = line_style[marker_idx][2]
            curve, = ax.plot(x_data, y_data, color=line_color,
                             linestyle=line_type, marker=marker, label=alg_name,
                             linewidth=1.5, markersize=8.0, markevery=max(min_data_len // 8, 1))
            if alg_name not in alg_to_line_handler:
                alg_to_line_handler[alg_name] = curve
            ax.fill_between(x_data, y_data - y_data_error, y_data + y_data_error, color=line_color, alpha=.2)
            if _col == 0:
                ax.set_ylabel(y_name, fontsize=plot_config.FONTSIZE_LABEL)

            ax.set_xlabel(x_name, fontsize=plot_config.FONTSIZE_LABEL)
            ax.tick_params(axis='x', labelsize=plot_config.FONTSIZE_XTICK)
            ax.tick_params(axis='y', labelsize=plot_config.FONTSIZE_YTICK)

            if plot_config.X_AXIS_SCI_FORM:
                ax.ticklabel_format(style='sci', scilimits=(-1, 2), axis='x')
                ax.xaxis.offsetText.set_fontsize(plot_config.FONTSIZE_YTICK)

            ax.set_title(sub_figure, fontsize=plot_config.FONTSIZE_TITLE)
            ax.grid(True)
            alg_count += 1
        if alg_count == 0:
            ax.set_title(sub_figure, fontsize=plot_config.FONTSIZE_TITLE)

        fig_ind += 1
    names = [k for k in alg_to_line_handler]
    curves = [v for k, v in alg_to_line_handler.items()]
    axarr[0][0].legend(handles=curves, labels=names, loc='center left', bbox_to_anchor=(plot_config.LEGEND_POSITION_X, plot_config.LEGEND_POSITION_Y),
                       ncol=plot_config.LEGEND_COLUMN, fontsize=plot_config.FONTSIZE_LEGEND)
    sup_title_name = y_name
    if plot_config.RECORD_DATE_TIME:
        sup_title_name += ': {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    plt.suptitle(sup_title_name, fontsize=plot_config.FONTSIZE_SUPTITLE, y=plot_config.SUPTITLE_Y)

    os.makedirs(plot_config.PLOT_FIGURE_SAVING_PATH, exist_ok=True)
    png_saving_path = os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, f'{y_name}.png')
    pdf_saving_path = os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, f'{y_name}.pdf')
    os.makedirs(os.path.dirname(png_saving_path), exist_ok=True)
    f.savefig(png_saving_path, bbox_inches='tight', dpi=plot_config.PNG_DPI)
    f.savefig(pdf_saving_path, bbox_inches='tight')
    return png_saving_path, x_name, y_name


def _plotting(data):
    sub_figure_content = [k for k in data]
    sub_figure_content = sorted(sub_figure_content, key=lambda x: x[0])
    print(f'total sub-figures: {sub_figure_content}')
    fig_row = int(np.ceil(len(sub_figure_content) / plot_config.MAX_COLUMN))
    fig_column = min(plot_config.MAX_COLUMN, len(sub_figure_content))
    fig_row = max(fig_row, 1)
    fig_column = max(fig_column, 1)
    figsize = (plot_config.SUBFIGURE_WIDTH * fig_column, plot_config.SUBFIGURE_HEIGHT * fig_row)
    print(f'making figure {fig_row} row {fig_column} col, size: {figsize}')
    random.seed(1)
    total_f = []
    total_png = []
    alg_to_color_idx = dict()
    for x_name, y_name in plot_config.PLOTTING_XY:
        for sub_figure in sub_figure_content:
            algs = [_alg for _alg in data[sub_figure]]
            algs = sorted(algs)
            for alg_name in algs:
                data_alg_list = data[sub_figure][alg_name]
                have_y_name = True
                for item in data_alg_list:
                    if y_name not in item['data']:
                        have_y_name = False
                if not have_y_name:
                    if y_name in data_alg_list[0]['data']:
                        print(f'path need to be check, alg_name: {alg_name}, {[item["folder_name"] for item in data_alg_list]}')
                    continue
                if alg_name not in alg_to_color_idx:
                    alg_idx = len(alg_to_color_idx)
                    alg_to_color_idx[alg_name] = alg_idx
                    style_num = len(line_style)
                    if alg_idx < style_num:
                        alg_to_color_idx[alg_name] = (alg_idx, alg_idx, alg_idx)
                    else:
                        alg_to_color_idx[alg_name] = (
                            random.randint(0, style_num - 1), random.randint(0, style_num - 1),
                            random.randint(0, style_num - 1))
    plotting_executor = ProcessPoolExecutor(max_workers=plot_config.PROCESS_NUM)
    futures = []
    for x_name, y_name in plot_config.PLOTTING_XY:
        plot_config_dict = {k: getattr(plot_config, k) for k in plot_config.global_plot_configs()}

        futures.append(plotting_executor.submit(_plot_sub_figure, data, fig_row,
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
    png_images = []
    from PIL import Image
    for png_file in total_png:
        print('load image from {}'.format(png_file))
        png_images.append(Image.open(png_file))
    cols = [image.size[0] for image in png_images]
    rows = [image.size[1] for image in png_images]
    max_col = max(cols)
    merge_png = Image.new('RGB', (max_col, sum(rows)), (255, 255, 255))
    for ind, png_file in enumerate(png_images):
        start_row = sum(rows[:ind])
        merge_png.paste(png_file, (0, start_row))
    total_png_output_path = os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, "total_curve.png")
    merge_png.save(total_png_output_path, "PNG")
    print(f'saving png to {total_png_output_path}')


def _overwrite_config(config):
    for k in plot_config.global_plot_configs():
        if k in config:
            if not config[k] == getattr(plot_config, k):
                print(f'config {k} in file is {config[k]}, '
                      f'which is {getattr(plot_config, k)} in code, overwrite it!')
                setattr(plot_config, k, config[k])


def overwrite_config(config_json_path):
    if config_json_path is not None:
        if os.path.exists(config_json_path):
            with open(config_json_path, 'r') as f:
                config = json.load(f)
                _overwrite_config(config)
        else:
            print(f'{config_json_path} not exists! load failed!')


def plot(config_json_path=None):
    overwrite_config(config_json_path)
    data = collect_data()
    _plotting(data)


if __name__ == '__main__':
    plot()
