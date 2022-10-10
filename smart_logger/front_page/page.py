import random
import sys, os

from flask import Flask, redirect, url_for, request, send_from_directory, send_file, render_template, make_response
import smart_logger.common.page_config as page_config
from smart_logger.util_logger.logger import Logger
import smart_logger.common.plot_config as plot_config
from smart_logger.front_page.experiment_data_loader import default_config, load_config, list_current_experiment, \
    get_parameter, reformat_dict, reformat_str, legal_path, save_config, list_current_configs,\
    make_config_type, analyze_experiment, delete_config_file, has_config, standardize_merger_item, get_record_data_item,\
    get_config_path, record_config_for_user
from smart_logger.report.plotting import plot as local_plot
from smart_logger.report.plotting import _overwrite_config, _str_to_short_name
from smart_logger.report.plotting import _make_table
import base64
import json
from flask_cors import CORS
import time
import os
import sys
from datetime import datetime, timedelta
from functools import wraps
import math
import threading


def get_project_path():
    return os.path.dirname(os.path.abspath(__file__))


def generate_code(num=20):
    code = ''
    for _ in range(num):
        code += chr(96 + random.randint(1, 26))
    return code


def in_cookie(key):
    if not page_config.REQUIRE_RELOGIN:
        cookie_dict = dict()
        # if key == 'user_name':
        #     cookie_dict['user_name'] = page_config.USER_NAME
        # elif key == 'cookie_code':
        #     cookie_dict['cookie_code'] = 'forever_code' if 'cookie_code' not in request.cookies else request.cookies[
        #         'cookie_code']
        # elif key == 'used_config':
        #     cookie_dict['used_config'] = _choose_config_init(
        #         page_config.USER_NAME, check_valid=False) if 'used_config' not in request.cookies else request.cookies['used_config']
        # return key in cookie_dict
        return key in ['user_name', 'cookie_code', 'used_config']
    return key in request.cookies


def query_cookie(key):
    if not page_config.REQUIRE_RELOGIN:
        cookie_dict = dict()
        if key == 'user_name':
            cookie_dict['user_name'] = page_config.USER_NAME
        elif key == 'cookie_code':
            cookie_dict['cookie_code'] = 'forever_code' if 'cookie_code' not in request.cookies else request.cookies[
            'cookie_code']
        elif key == 'used_config':
            cookie_dict['used_config'] = _choose_config_init(
            page_config.USER_NAME, check_valid=False) if 'used_config' not in request.cookies else request.cookies['used_config']
            if not has_config(cookie_dict['used_config']):
                cookie_dict['used_config'] = _choose_config_init(page_config.USER_NAME, check_valid=False)
        return cookie_dict[key]
    res = request.cookies[key] if key in request.cookies else None
    return res


def require_login(source_name='', allow_guest=False):
    def func_output(func_in):
        @wraps(func_in)
        def wrapper(*args, **kwargs):
            user_data = make_user_data()
            check_flag = check_user(user_data, allow_guest=allow_guest)
            Logger.logger(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: check done')
            if not check_flag:
                Logger.logger(f'user is not valid, redirect from {source_name} to login page')
                return redirect_login_page(source_name)
            return func_in(*args, **kwargs)

        return wrapper

    return func_output


app = Flask(__name__, template_folder=os.path.join(
    get_project_path(), 'template'), root_path=get_project_path())
CORS(app)


def make_user_data():
    user_data = dict()
    for item in request.args:
        user_data[item] = request.args[item]
    if 'name' not in user_data and in_cookie('user_name'):
        user_data['name'] = query_cookie('user_name')
    return user_data


def check_user(user_data, allow_guest=False):
    Logger.logger(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: check user {user_data}')
    if in_cookie('user_name') and in_cookie('cookie_code') and in_cookie('used_config'):
        if not has_config(query_cookie('used_config')):
            Logger.logger(f'config file {query_cookie("used_config")} not exists!!!')
            return False
        _user_name = query_cookie('user_name')
        _code = query_cookie('cookie_code')
        if 'name' not in user_data or not user_data['name'] == _user_name:
            user_data['name'] = _user_name
        return True
    else:
        Logger.logger(f'cookies do not exist or cookies are not complete: {request.cookies}!')
        return False


def redirect_login_page(source=''):
    url = url_for('start_page')
    if len(source) > 0:
        url = url + "?from_page=source"
    return redirect(url)


# 原始网页，若已经登录，直接进入实验数据页面
@app.route('/', methods=['GET'])
def hello():
    user_data = make_user_data()
    user_valid = check_user(user_data, allow_guest=True)
    if user_valid:
        return redirect('/experiment')
    args = dict()
    for item in request.args:
        args[item] = request.args[item]
    source = args['from'] if 'from' in args else ''
    return render_template('t_hello.html', source=source)


# 登录界面，必须登录
@app.route('/start', methods=['GET'])
def start_page():
    args = dict()
    for item in request.args:
        args[item] = request.args[item]
    Logger.logger(f'start args: {args}!!')
    source = args['from_page'] if 'from' in args else ''
    return render_template('t_hello.html', source=source)


# 下线
@app.route('/logout', methods=['GET'])
def logout():
    user_data = make_user_data()
    check_user(user_data, allow_guest=True)
    response = make_response(redirect(url_for('start_page')))
    if 'name' in user_data:
        response.set_cookie('user_name', '', 0)
        response.set_cookie('cookie_code', '', 0)
    return response


def _choose_config_init(user_name, check_valid=True):
    candidate_config = []
    for item in list_current_configs():
        candidate_config.append(item)
    Logger.logger(f'found configs: {candidate_config}')

    if len(candidate_config) == 0:
        if load_config('default_config.json') is None:
            save_config(default_config(), 'default_config.json')
        config = load_config('default_config.json')
        config_name = 'config-{}-{}-{}.json'.format(user_name,
                                                    datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), generate_code(10))
        save_config(config, config_name)
    else:
        user_history_data_path = os.path.join(page_config.USER_DATA_PATH, f'{user_name}.json')
        if os.path.exists(user_history_data_path):
            user_config_data = json.load(open(user_history_data_path, 'r'))
            if "config" in user_config_data and user_config_data['config'] in candidate_config:
                config_name = user_config_data['config']
            else:
                config_name = candidate_config[-1]
        else:
            config_name = candidate_config[-1]
        if check_valid:
            config = load_config(config_name)
            if config is None:
                config = load_config('default_config.json')
                config_name = 'config-{}-{}-{}.json'.format(query_cookie('user_name'),
                                                            datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                                                            generate_code(10))
                save_config(config, config_name)
    return config_name

# 判断是否能够登录的服务
@app.route('/login_direct', methods=['POST'])
def login_post_direct():
    user_data = dict()
    for k, v in request.form.items():
        user_data[k] = v
    Logger.logger(f'user_data: {user_data}')
    if 'nm' not in user_data or 'passwd' not in user_data or 'from' not in user_data:
        return redirect_login_page()
    if '.' in user_data['nm'] or '/' in user_data['nm']:
        return False
    result = user_data['nm'] == page_config.USER_NAME and user_data['passwd'] == page_config.PASSWD
    if not page_config.REQUIRE_RELOGIN:
        result = True
        user_data['nm'] = page_config.USER_NAME
        user_data['passwd'] = page_config.PASSWD
    # result = len(user_data['nm']) > 0 and len(user_data['passwd']) > 0
    user_name = user_data['nm']

    if result:
        source_page = user_data['from'] if 'from' in user_data else None
        if source_page is not None and len(source_page) > 0:
            target_page = source_page
        else:
            target_page = 'experiment'
        Logger.logger(f'redirect to {target_page}')
        outdate = datetime.now() + timedelta(hours=page_config.COOKIE_PERIOD)
        response = make_response(redirect(target_page))
        response.set_cookie('user_name', user_name, expires=outdate)
        code = generate_code(20)
        response.set_cookie('cookie_code', code, expires=outdate)
        outdate_config_path = datetime.now() + timedelta(hours=page_config.COOKIE_PERIOD)
        config_name = _choose_config_init(user_data['nm'])
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
        return response
    else:
        Logger.logger(f'validate failed: {user_data}')
    return redirect_login_page()


# 进入实验界面
@app.route("/experiment", methods=['GET'])
@require_login(source_name='experiment', allow_guest=True)
def experiment():
    # return "Hello World"
    # config = load_config('1.json')
    # return str(config)
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    _overwrite_config(config)
    exp_folders = list_current_experiment()
    exp_folders_code = [base64.urlsafe_b64encode(item.encode()).decode() for item in exp_folders]
    return render_template('t_experiment.html', exp_folder_list=exp_folders, exp_folders_code=exp_folders_code)


def csv_to_html(dataframe):
    pass

@app.route("/experiment_parameter/<folder_name>", methods=['GET'])
@require_login(source_name='experiment_parameter', allow_guest=True)
def obtain_experiment_parameter(folder_name):
    folder_name = base64.urlsafe_b64decode(folder_name.encode()).decode()
    # return "Hello World"
    param, dtree, full_path, name, filesize, important_configs = get_parameter(folder_name)
    if param is None:
        return redirect('/experiment')
    if full_path is not None:
        for i in range(len(full_path)):
            if full_path[i] is not None:
                full_path[i] = base64.urlsafe_b64encode(os.path.join(os.path.dirname(folder_name), full_path[i]).encode()).decode()
            else:
                full_path[i] = 'None'

    dtree_desc = reformat_str(dtree)
    param_desc = reformat_dict(param)
    important_configs = reformat_dict(important_configs)
    recorded_data, data_length, csv_data_df = get_record_data_item(folder_name)
    if csv_data_df is not None:
        html_code = csv_data_df.to_html(classes='data', header=True, show_dimensions=False, max_rows=1000);
        html_code = '\n'.join(html_code.split('\n')[1:])

        html_code = '<table border="1" align="center" frame="hsides" rules="rows" table-layout="fixed">\n' + html_code
        html_code = f'<p> {csv_data_df.shape[0]} rows × {csv_data_df.shape[1]} columns  </p>' + html_code
        tables = [html_code]
        show_table=True

    else:
        tables = []
        show_table = False

    return render_template('t_parameter_display.html',
                           experiment_description=param_desc,
                           dtree_desc=dtree_desc,
                           name=folder_name,
                           full_path=full_path,
                           filenames=name,
                           important_configs=important_configs,
                           filesize=filesize,
                           recorded_data=recorded_data,
                           data_length=data_length,
                           tables=tables,
                           show_table=show_table)


@app.route("/experiment_data_download/<folder_name>/<attach>", methods=['GET'])
@require_login(source_name='experiment_data_download', allow_guest=True)
def experiment_data_download(folder_name, attach):
    # return "Hello World"
    folder_name = base64.urlsafe_b64decode(folder_name.encode()).decode()
    file_name = os.path.join(plot_config.PLOT_LOG_PATH, folder_name)
    if not legal_path(file_name):
        Logger.logger(f'file {file_name} is not legal')
        return render_template('404.html')
    if os.path.exists(file_name):
        Logger.logger(f'file {file_name} exists')
        file_name = os.path.abspath(file_name)
        filename = os.path.basename(file_name)
        dirname = os.path.dirname(file_name)

        # as_attachment = True if not (
        #             filename.lower().endswith('png') or filename.lower().endswith('jpg') or filename.lower().endswith(
        #         'txt') or filename.lower().endswith('json')) else False
        as_attachment = True if int(attach) == 1 else False
        return send_from_directory(dirname, filename, as_attachment=as_attachment)

    else:
        Logger.logger(f'file {file_name} does not exist')
        return render_template('404.html')


@app.route("/plot", methods=['GET'])
@require_login(source_name='plot', allow_guest=True)
def plot():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    _overwrite_config(config)
    config_ordered = {k: config[k] for k in plot_config.global_plot_configs() if k in config}
    added_key = []
    for k in config:
        if k not in config_ordered:
            added_key.append(k)
    for k in added_key:
        config_ordered[k] = config[k]

    config_ordered = {k: v for k, v in config_ordered.items() if k not in ['SHORT_NAME_FROM_CONFIG', 'DATA_IGNORE', 'DATA_MERGER',
                                                           'PLOTTING_XY', 'FIGURE_TO_SYNC', 'FIGURE_SEPARATION',
                                                           'DATA_KEY_RENAME_CONFIG', 'DESCRIPTION',
                                                           'LOG_DIR_BACKING_NAME', 'DATA_PATH',
                                                           'PLOT_FIGURE_SAVING_PATH', 'FIGURE_SERVER_MACHINE_IP',
                                                           'FIGURE_SERVER_MACHINE_PORT', 'FIGURE_SERVER_MACHINE_USER',
                                                           'FIGURE_SERVER_MACHINE_PASSWD',
                                                           'FIGURE_SERVER_MACHINE_TARGET_PATH', 'PLOTTING_ORDER',
                                                           'LEGEND_ORDER', 'DATA_SELECT', 'USE_IGNORE_RULE',
                                                           'TABLE_BOLD_MAX', 'DATA_IGNORE_PROPERTY',
                                                           'DATA_SELECT_PROPERTY', 'DATA_IGNORE_GARBAGE',
                                                           'DATA_SELECT_GARBAGE', 'DATA_IGNORE_PROPERTY_GARBAGE',
                                                           'DATA_SELECT_PROPERTY_GARBAGE',
                                                           'SHORT_NAME_FROM_CONFIG_PROPERTY']}
    config = config_ordered
    config_description = plot_config.DESCRIPTION
    for k in config:
        if k not in config_description:
            config_description[k] = 'None'
    config_type = make_config_type(config)
    config_file_list = list_current_configs()
    target_file = os.path.join(page_config.WEB_RAM_PATH, page_config.TOTAL_FIGURE_FOLDER + "_tmp",
                               f'{config_name}.png')
    initial_figure_url = '#'
    if os.path.exists(target_file):
        Logger.logger(f'{target_file} exists, return it first')
        file_name = os.path.basename(target_file)
        initial_figure_url = url_for('lst_output_figure')
        initial_figure_url = initial_figure_url + f'?rand={random.random()}&file_name={file_name}'
    else:
        Logger.logger(f'{target_file} does not exist, leave it EMPTY.')
    file_list = []
    if config_name.endswith('.json'):
        figure_saving_path = os.path.join(page_config.FIGURE_PATH, query_cookie('user_name'), config_name[:-5])
    else:
        figure_saving_path = os.path.join(page_config.FIGURE_PATH, query_cookie('user_name'), config_name)
    if os.path.exists(figure_saving_path) and os.path.isdir(figure_saving_path):
        file_list = []
        for root, dirs, files in os.walk(figure_saving_path, followlinks=True):
            for file in files:
                if file.endswith('pdf') or file.endswith('png'):
                    full_name = os.path.join(root, file)
                    file_list.append(os.path.relpath(full_name, figure_saving_path))
    file_list = sorted(file_list, key=lambda x: x.split('.')[-1])
    file_list_encode = [base64.urlsafe_b64encode(os.path.join(item).encode()).decode() for item in file_list]

    return render_template('t_plot.html',
                             plot_config=config,   # plot_config list list
                           config_type=config_type,
                             config_name=config_name,
                           description=config_description,
                           config_file_list=config_file_list,
                           initial_figure_url=initial_figure_url,
                           file_list=file_list,
                           file_list_encode=file_list_encode,
                           )



@app.route("/query_pregenerated_file/<file_name>/<attach>", methods=['GET'])
@require_login(source_name='query_pregenerated_file', allow_guest=True)
def query_pregenerated_file(file_name, attach):
    config_name = query_cookie('used_config')
    if config_name.endswith('.json'):
        figure_saving_path = os.path.join(page_config.FIGURE_PATH, query_cookie('user_name'), config_name[:-5])
    else:
        figure_saving_path = os.path.join(page_config.FIGURE_PATH, query_cookie('user_name'), config_name)
    figure_saving_path = os.path.abspath(figure_saving_path)
    file_name = base64.urlsafe_b64decode(file_name.encode()).decode()

    if not os.path.exists(os.path.join(figure_saving_path, file_name)):
        return render_template('404.html')
    as_attach = True if int(attach) == 1 else False
    return send_from_directory(figure_saving_path, file_name, as_attachment=as_attach)

@app.route("/table", methods=['GET'])
@require_login(source_name='table', allow_guest=True)
def table():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    config_file_list = list_current_configs()
    return render_template('t_table.html',
                             plot_config=config,   # plot_config list list
                             config_name=config_name,
                             config_file_list=config_file_list,
                             bold_max=config['TABLE_BOLD_MAX'])


@app.route("/query_table", methods=['GET'])
@require_login(source_name='query_table', allow_guest=True)
def query_table():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    _overwrite_config(config)
    result = _make_table()
    return result


@app.route("/query_table_source/<use_latex>", methods=['GET'])
@require_login(source_name='query_table_source', allow_guest=True)
def query_table_source(use_latex):
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    _overwrite_config(config)
    result = _make_table(True if str(use_latex) == 'True' else False)
    # result = result.replace('\n', '<br/>')
    result = f'<br/><pre><code>\n{result}</code></pre>\n<br/>'
    Logger.logger(f'source code {use_latex}: {result}')
    return result


def data_convert(data, origin_data):
    if origin_data is None:
        return data
    elif isinstance(origin_data, float):
        return float(data)
    elif isinstance(origin_data, int):
        return int(data)
    elif isinstance(origin_data, str):
        return str(data)
    elif isinstance(origin_data, bool):
        return str(data) == 'True'
    return data


@app.route("/plot_config_update", methods=['POST'])
@require_login(source_name='plot_config_update', allow_guest=True)
def plot_config_update():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    config_type = make_config_type(config)
    for k, v in request.form.items():
        k_split = k.split(':')
        if len(k_split) == 1:
            _type = config_type[k]
            if not str(v) == str(config[k]):
                if _type == 'bool':
                    config[k] = True if str(v) == 'True' else False
                elif _type == 'float':
                    config[k] = float(v)
                elif _type == 'int':
                    config[k] = int(v)
                elif _type == 'str':
                    if k == 'PLOT_LOG_PATH':
                        v_ = str(v)
                        while v_[-1] == '/':
                            v_ = v_[:-1]
                        v = v_
                    config[k] = str(v)
                else:
                    raise NotImplementedError(f'type {_type} not implemented!')
        else:
            k_main = k_split[0]
            _type = config_type[k_main]
            if _type == 'list':
                k_sub = int(k_split[1])
                config[k_main][k_sub] = data_convert(v, config[k_main][k_sub])
            elif _type == 'tuple':
                k_sub = int(k_split[1])
                data = config[k_main]
                data = list(data)
                data[k_sub] = data_convert(v, data[k_sub])
                data = tuple(data)
                config[k_main] = data
            else:
                raise NotImplementedError(f'type {_type} not implemented')
        Logger.logger(f'plot config update: {k} {v}')
    save_config(config, config_name)
    return redirect('/plot', code=204)



@app.route("/exp_figure", methods=['GET'])
@require_login(source_name='exp_figure', allow_guest=True)
def exp_figure():
    start_time = time.time()
    config_name = query_cookie('used_config')
    if config_name.endswith('.json'):
        output_path = os.path.join(page_config.FIGURE_PATH, query_cookie('user_name'), config_name[:-5])
    else:
        output_path = os.path.join(page_config.FIGURE_PATH, query_cookie('user_name'), config_name)
    output_path = os.path.abspath(output_path)
    config = load_config(config_name)
    config['PLOT_FIGURE_SAVING_PATH'] = output_path
    save_config(config, config_name)
    config_path = get_config_path(config_name)
    Logger.logger(f'plot figure according to {config_path}, figure save to {output_path}')
    local_plot(config_path)
    saving_png = f'{os.path.join(output_path, plot_config.FINAL_OUTPUT_NAME)}.png'
    Logger.logger(f'return figure {saving_png}, drawing cost {time.time() - start_time}')
    target_folder = os.path.join(page_config.WEB_RAM_PATH, page_config.TOTAL_FIGURE_FOLDER, f'{plot_config.FINAL_OUTPUT_NAME}.png')
    target_folder_tmp = os.path.join(page_config.WEB_RAM_PATH, page_config.TOTAL_FIGURE_FOLDER + "_tmp", f'{config_name}.png')

    Logger.logger(f'cp {saving_png} {target_folder}')
    os.makedirs(os.path.dirname(target_folder), exist_ok=True)
    os.makedirs(os.path.dirname(target_folder_tmp), exist_ok=True)
    os.system(f'cp \"{saving_png}\" \"{target_folder}\"')
    os.system(f'cp \"{saving_png}\" \"{target_folder_tmp}\"')
    return send_from_directory(output_path, f'{plot_config.FINAL_OUTPUT_NAME}.png', as_attachment=False)


@app.route("/lst_output_figure", methods=['GET'])
@require_login(source_name='lst_output_figure', allow_guest=True)
def lst_output_figure():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    _overwrite_config(config)
    target_file = os.path.join(page_config.WEB_RAM_PATH, page_config.TOTAL_FIGURE_FOLDER + "_tmp", f'{config_name}.png')
    target_file = os.path.abspath(target_file)
    target_dir = os.path.dirname(target_file)
    file_name = os.path.basename(target_file)
    Logger.logger(f'dir: {target_dir}, name: {file_name}, exists: {os.path.exists(target_file)}')
    return send_from_directory(target_dir, file_name, as_attachment=False)


@app.route("/param_adjust", methods=['GET'])
@require_login(source_name='param_adjust', allow_guest=True)
def param_adjust():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    _overwrite_config(config)
    data_ignore = [] if 'DATA_IGNORE' not in config else config['DATA_IGNORE']
    data_ignore_garbage = [] if 'DATA_IGNORE_GARBAGE' not in config else config['DATA_IGNORE_GARBAGE']
    data_ignore_property = [] if 'DATA_IGNORE_PROPERTY' not in config else config['DATA_IGNORE_PROPERTY']
    data_choose = [] if 'DATA_SELECT' not in config else config['DATA_SELECT']
    data_choose_garbage = [] if 'DATA_SELECT_GARBAGE' not in config else config['DATA_SELECT_GARBAGE']
    data_choose_property = [] if 'DATA_SELECT_PROPERTY' not in config else config['DATA_SELECT_PROPERTY']
    data_merge = [] if 'DATA_MERGER' not in config else config['DATA_MERGER']
    data_short_name_dict = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    data_short_name_property = {} if 'SHORT_NAME_FROM_CONFIG_PROPERTY' not in config else config['SHORT_NAME_FROM_CONFIG_PROPERTY']
    Logger.local_log(f'start analyze_experiment')
    start_time = time.time()
    exp_data, exp_data_ignores, selected_choices, possible_config_ignore, selected_choices_ignore, alg_idxs_ignore, \
        folder_ignore, nick_name_ignore_list, alg_idx, possible_config, \
            short_name_to_ind, nick_name_list = analyze_experiment(need_ignore=config['USE_IGNORE_RULE'],
                                                                   data_ignore=data_ignore,
                                                                   need_select=not config['USE_IGNORE_RULE'],
                                                                   data_select=data_choose,
                                                                   data_merge=data_merge,
                                                                   data_short_name_dict=data_short_name_dict,
                                                                   data_ignore_property=data_ignore_property,
                                                                   data_select_property=data_choose_property,
                                                                   data_short_name_property=data_short_name_property)
    Logger.local_log(f'finish analyze_experiment {time.time() - start_time}')

    exp_data_encoded = [base64.urlsafe_b64encode(item.encode()).decode() for item in exp_data]
    exp_data_ignores_encoded = [base64.urlsafe_b64encode(item.encode()).decode() for item in exp_data_ignores]
    Logger.logger(f'selected_choices keys: {[k for k in selected_choices]}')
    merge_choices = [] if 'DATA_MERGER' not in config else config['DATA_MERGER']
    merge_config_file = dict()
    for k in possible_config:
        if k in merge_choices:
            merge_config_file[k] = [True, len(possible_config[k])]
        else:
            merge_config_file[k] = [False, len(possible_config[k])]
    possible_config_keys_list = [k for k in possible_config]
    merge_config_file = [(k, v[0], v[1]) for k, v in merge_config_file.items()]
    merge_config_file = list(sorted(sorted(sorted(merge_config_file, key=lambda x: x[0]), key=lambda x: x[1], reverse=True), key=lambda x: x[2], reverse=True))
    selected_config_list = [(k, v, len(v)) for k, v in possible_config.items()]
    if plot_config.USE_IGNORE_RULE:
        for k in possible_config:
            possible_config[k] = sorted(possible_config[k], key=lambda x: str(x))
        possible_config = [(k, v) for k, v in possible_config.items()]
    else:
        for k in possible_config_ignore:
            possible_config_ignore[k] = sorted(possible_config_ignore[k], key=lambda x: str(x))
        possible_config = [(k, v) for k, v in possible_config_ignore.items()]

    possible_config = list(sorted(sorted(possible_config, key=lambda x: x[0]), key=lambda x: len(x[1]), reverse=True))
    selected_config_list = list(sorted(sorted(selected_config_list, key=lambda x: x[0]), key=lambda x: len(x[1]), reverse=True))
    # Logger.local_log('possible config', possible_config)
    # Logger.logger(f'possible config json: {json.dumps(possible_config)}')
    encode_possible_config_js = base64.urlsafe_b64encode(json.dumps(possible_config).encode()).decode()
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    rename_rule_dict = rename_rule
    possible_short_name = sorted([k for k in short_name_to_ind if not _str_to_short_name(k, rename_rule,
                                                                                     config['SHORT_NAME_FROM_CONFIG_PROPERTY'])[1]])
    rename_rule = [(k, v) for k, v in rename_rule.items()]
    rename_rule = sorted(rename_rule, key=lambda x: x[0])
    plotting_xy = [] if 'PLOTTING_XY' not in config else config['PLOTTING_XY']
    config_file_list = list_current_configs()
    rename_rule_data = dict() if 'DATA_KEY_RENAME_CONFIG' not in config else config['DATA_KEY_RENAME_CONFIG']
    rename_rule_data = sorted([(k, v) for k, v in rename_rule_data.items()])
    separators = [] if 'FIGURE_SEPARATION' not in config else config['FIGURE_SEPARATION']
    separators = separators
    nick_name_set = set(nick_name_list)
    Logger.logger(f'nick name set: {nick_name_set}')

    exists_ordered_curves = plot_config.PLOTTING_ORDER
    remain_unordered_curves = [item for item in nick_name_set if item not in exists_ordered_curves]
    exists_ordered_curves_encode = [base64.urlsafe_b64encode(item.encode()).decode() for item in exists_ordered_curves]
    remain_unordered_curves_encode = [base64.urlsafe_b64encode(item.encode()).decode() for item in remain_unordered_curves]
    total_curves = exists_ordered_curves + remain_unordered_curves
    total_curves = [item for item in total_curves if item in nick_name_set]
    exists_ordered_legends = plot_config.LEGEND_ORDER
    exists_unordered_legends = [item for item in total_curves if item not in exists_ordered_legends]
    exists_ordered_legends_encode = [base64.urlsafe_b64encode(item.encode()).decode() for item in exists_ordered_legends]
    exists_unordered_legends_encode = [base64.urlsafe_b64encode(item.encode()).decode() for item in exists_unordered_legends]
    return render_template('t_param_adapt.html',
                           exp_data=exp_data,
                           exp_data_encoded=exp_data_encoded,
                           exp_data_ignores=exp_data_ignores,
                           exp_data_ignores_encoded=exp_data_ignores_encoded,
                           selected_choices=selected_choices,
                           merge_config_file=merge_config_file,  # merge_config_file list list
                           alg_idx=alg_idx,
                           alg_idxs_ignore=alg_idxs_ignore,
                           data_ignore=data_ignore,  # data_ignore list list
                           rename_rule_dict=rename_rule_dict,
                           possible_config=possible_config,
                           possible_config_js=encode_possible_config_js,
                           possible_config_keys_list=possible_config_keys_list,
                           rename_rule=rename_rule,  # rename_rule list list
                           plotting_xy=plotting_xy,  # plotting_xy list list
                           possible_short_name=possible_short_name,
                           nick_name_list=nick_name_list,
                           nick_name_ignore_list=nick_name_ignore_list,
                           config_file_list=config_file_list,
                           config_name=config_name,
                           rename_rule_data=rename_rule_data,
                           separators=separators,
                           exists_ordered_curves=exists_ordered_curves,
                           remain_unordered_curves=remain_unordered_curves,
                           exists_ordered_curves_encode=exists_ordered_curves_encode,
                           remain_unordered_curves_encode=remain_unordered_curves_encode,
                           exists_ordered_legends=exists_ordered_legends,
                           exists_unordered_legends=exists_unordered_legends,
                           exists_ordered_legends_encode=exists_ordered_legends_encode,
                           exists_unordered_legends_encode=exists_unordered_legends_encode,
                           filter_data_with_ignore=plot_config.USE_IGNORE_RULE,
                           data_choose_rule=data_choose,
                           selected_config_list=selected_config_list,
                           data_ignore_garbage=data_ignore_garbage,
                           data_choose_garbage=data_choose_garbage
                           )



@app.route("/merge_process", methods=['POST'])
@require_login(source_name='merge_process', allow_guest=True)
def merge_process():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    new_merger = [k for k in request.form]
    config['DATA_MERGER'] = new_merger
    save_config(config, config_name)
    return redirect('param_adjust')



@app.route("/choose_config/<source>", methods=['POST'])
@require_login(source_name='choose_config', allow_guest=True)
def choose_config(source):
    if source == 'adapt':
        response = make_response(redirect('/param_adjust'))
    elif source == 'plot':
        response = make_response(redirect('/plot'))
    elif source == 'table':
        response = make_response(redirect('/table'))
    else:
        raise NotImplementedError(f'{source} has not been implemented')

    outdate_config_path = datetime.now() + timedelta(hours=page_config.COOKIE_PERIOD)
    config_name = request.form.get('chosen_config', None)
    if config_name is not None:
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
        record_config_for_user(query_cookie('user_name'), config_name)
    return response

@app.route("/rename_config", methods=['POST'])
@require_login(source_name='rename_config', allow_guest=True)
def rename_config():
    response = make_response(redirect('param_adjust'))
    config_name = query_cookie('used_config')
    config_name_legacy = config_name
    config = load_config(config_name)
    outdate_config_path = datetime.now() + timedelta(hours=page_config.COOKIE_PERIOD)
    config_name = request.form.get('rename', None)
    config_name = config_name.replace('/', '-')
    if config_name is not None and len(config_name) > 0:
        delete_config_file(config_name_legacy)
        save_config(config, config_name)
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
        record_config_for_user(query_cookie('user_name'), config_name)
    return response

@app.route("/create_config", methods=['GET'])
@require_login(source_name='create_config', allow_guest=True)
def create_config():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    config_name = 'config-{}-{}-{}.json'.format(query_cookie('user_name'),
                                                datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                                                generate_code(10))
    save_config(config, config_name)
    response = make_response(redirect('param_adjust'))
    outdate_config_path = datetime.now() + timedelta(hours=page_config.COOKIE_PERIOD)
    response.set_cookie('used_config', config_name, expires=outdate_config_path)
    record_config_for_user(query_cookie('user_name'), config_name)
    return response


@app.route("/delete_config", methods=['POST'])
@require_login(source_name='delete_config', allow_guest=True)
def delete_config():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    delete_file = json.loads(request.data.decode())['delete_config']
    delete_config_file(delete_file)
    response = make_response(redirect('param_adjust'))

    if delete_file == config_name:
        config_list = list_current_configs()
        if len(config_list) == 0:
            config_name = 'config-{}-{}-{}.json'.format(query_cookie('user_name'),
                                                        datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                                                        generate_code(10))

            save_config(config, config_name)
        else:
            config_name = config_list[-1]
        outdate_config_path = datetime.now() + timedelta(hours=page_config.COOKIE_PERIOD)
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
        record_config_for_user(query_cookie('user_name'), config_name)

    return response

@app.route("/reset_config", methods=['GET'])
@require_login(source_name='reset_config', allow_guest=True)
def reset_config():
    config = load_config('default_config.json')
    if config is None:
        config = default_config()
    config_name = query_cookie('used_config')
    save_config(config, config_name)
    return redirect('param_adjust')


def _generate_grid_analyze_result(config_name):
    config = load_config(config_name)
    all_data_merger = config['DATA_MERGER'] if 'DATA_MERGER' in config else []
    for merger in all_data_merger:
        config['DATA_MERGER'] = [merger]
        config['REPORT_PCA_EVAL'] = True
        merger_formal = merger.replace('/', '-')
        save_config(config, f'{config_name}_gs_{merger_formal}')

@app.route("/merge_config", methods=['POST'])
@require_login(source_name='merge_config', allow_guest=True)
def merge_config():
    config_target = load_config(request.form['target_config'])
    if config_target is None:
        config_target = default_config()
    config_name = query_cookie('used_config')
    config_current = load_config(config_name)
    for k in config_current:
        if k in config_target:
            config_current[k] = config_target[k]
    for k in config_target:
        if k not in config_current:
            config_current[k] = config_target[k]
    save_config(config_current, config_name)
    return redirect('param_adjust')


@app.route("/grid_config_generate", methods=['GET'])
@require_login(source_name='grid_config_generate', allow_guest=True)
def grid_config_generate():
    config_name = query_cookie('used_config')
    _generate_grid_analyze_result(config_name)
    return redirect('param_adjust')


@app.route("/add_ignore", methods=['POST'])
@require_login(source_name='add_ignore', allow_guest=True)
def add_ignore():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    newly_added_ignore = json.loads(request.data.decode())
    if 'USE_IGNORE_RULE' in config and config['USE_IGNORE_RULE']:
        if 'DATA_IGNORE' not in config:
            config['DATA_IGNORE'] = []
        if len(newly_added_ignore) > 0:
            ignore_dict = {k: newly_added_ignore[k]['value'] for k in newly_added_ignore}
            config['DATA_IGNORE'].append(ignore_dict)
            ignore_desc = dict()
            for k in newly_added_ignore:
                ignore_desc[k] = dict()
                for k2 in newly_added_ignore[k]:
                    if not k2 == 'value':
                        ignore_desc[k][k2] = newly_added_ignore[k][k2]
            config['DATA_IGNORE_PROPERTY'].append(ignore_desc)
    else:
        if 'DATA_SELECT' not in config:
            config['DATA_SELECT'] = []
        if len(newly_added_ignore) > 0:
            select_dict = {k: newly_added_ignore[k]['value'] for k in newly_added_ignore}
            config['DATA_SELECT'].append(select_dict)
            ignore_desc = dict()
            for k in newly_added_ignore:
                ignore_desc[k] = dict()
                for k2 in newly_added_ignore[k]:
                    if not k2 == 'value':
                        ignore_desc[k][k2] = newly_added_ignore[k][k2]
            config['DATA_SELECT_PROPERTY'].append(ignore_desc)
    save_config(config, config_name)
    return redirect('param_adjust')


@app.route("/del_ignore/<rule_idx>/<move_to_garbage>", methods=['GET'])
@require_login(source_name='del_ignore', allow_guest=True)
def del_ignore(rule_idx, move_to_garbage):
    move_to_garbage = int(move_to_garbage) == 1
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if move_to_garbage:
        rule_idx = int(rule_idx)
        if config['USE_IGNORE_RULE']:
            item = config['DATA_IGNORE'][rule_idx]
            item_property = config['DATA_IGNORE_PROPERTY'][rule_idx]
            config['DATA_IGNORE'] = [config['DATA_IGNORE'][i] for i in range(len(config['DATA_IGNORE'])) if
                                     not str(i) == str(rule_idx)]
            config['DATA_IGNORE_PROPERTY'] = [config['DATA_IGNORE_PROPERTY'][i] for i in
                                              range(len(config['DATA_IGNORE_PROPERTY'])) if not str(i) == str(rule_idx)]
            config['DATA_IGNORE_GARBAGE'].append(item)
            config['DATA_IGNORE_PROPERTY_GARBAGE'].append(item_property)
        else:
            item = config['DATA_SELECT'][rule_idx]
            item_property = config['DATA_SELECT_PROPERTY'][rule_idx]
            config['DATA_SELECT'] = [config['DATA_SELECT'][i] for i in range(len(config['DATA_SELECT'])) if
                                     not str(i) == str(rule_idx)]
            config['DATA_SELECT_PROPERTY'] = [config['DATA_SELECT_PROPERTY'][i] for i in
                                              range(len(config['DATA_SELECT_PROPERTY'])) if not str(i) == str(rule_idx)]
            config['DATA_SELECT_GARBAGE'].append(item)
            config['DATA_SELECT_PROPERTY_GARBAGE'].append(item_property)

    else:
        if 'USE_IGNORE_RULE' in config and config['USE_IGNORE_RULE']:
            if 'DATA_IGNORE' not in config:
                config['DATA_IGNORE'] = []
            else:
                config['DATA_IGNORE'] = [config['DATA_IGNORE'][i] for i in range(len(config['DATA_IGNORE'])) if not str(i) == str(rule_idx)]
                config['DATA_IGNORE_PROPERTY'] = [config['DATA_IGNORE_PROPERTY'][i] for i in range(len(config['DATA_IGNORE_PROPERTY'])) if not str(i) == str(rule_idx)]
        else:
            if 'DATA_SELECT' not in config:
                config['DATA_SELECT'] = []
            else:
                config['DATA_SELECT'] = [config['DATA_SELECT'][i] for i in range(len(config['DATA_SELECT'])) if not str(i) == str(rule_idx)]
                config['DATA_SELECT_PROPERTY'] = [config['DATA_SELECT_PROPERTY'][i] for i in range(len(config['DATA_SELECT_PROPERTY'])) if not str(i) == str(rule_idx)]
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/del_garbage/<rule_idx>/<move_back>", methods=['GET'])
@require_login(source_name='del_ignore', allow_guest=True)
def del_garbage(rule_idx, move_back):
    move_back = int(move_back) == 1
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if move_back:
        rule_idx = int(rule_idx)
        if config['USE_IGNORE_RULE']:
            item = config['DATA_IGNORE_GARBAGE'][rule_idx]
            item_property = config['DATA_IGNORE_PROPERTY_GARBAGE'][rule_idx]
            config['DATA_IGNORE'].append(item)
            config['DATA_IGNORE_PROPERTY'].append(item_property)
            config['DATA_IGNORE_GARBAGE'] = [config['DATA_IGNORE_GARBAGE'][i] for i in
                                             range(len(config['DATA_IGNORE_GARBAGE'])) if not str(i) == str(rule_idx)]
            config['DATA_IGNORE_PROPERTY_GARBAGE'] = [config['DATA_IGNORE_PROPERTY_GARBAGE'][i] for i in
                                                      range(len(config['DATA_IGNORE_PROPERTY_GARBAGE'])) if
                                                      not str(i) == str(rule_idx)]
        else:
            item = config['DATA_SELECT_GARBAGE'][rule_idx]
            item_property = config['DATA_SELECT_PROPERTY_GARBAGE'][rule_idx]
            config['DATA_SELECT'].append(item)
            config['DATA_SELECT_PROPERTY'].append(item_property)
            config['DATA_SELECT_GARBAGE'] = [config['DATA_SELECT_GARBAGE'][i] for i in
                                             range(len(config['DATA_SELECT_GARBAGE'])) if not str(i) == str(rule_idx)]
            config['DATA_SELECT_PROPERTY_GARBAGE'] = [config['DATA_SELECT_PROPERTY_GARBAGE'][i] for i in
                                                      range(len(config['DATA_SELECT_PROPERTY_GARBAGE'])) if
                                                      not str(i) == str(rule_idx)]
    else:
        if 'USE_IGNORE_RULE' in config and config['USE_IGNORE_RULE']:
            if 'DATA_IGNORE_GARBAGE' not in config:
                config['DATA_IGNORE_GARBAGE'] = []
            else:
                config['DATA_IGNORE_GARBAGE'] = [config['DATA_IGNORE_GARBAGE'][i] for i in range(len(config['DATA_IGNORE_GARBAGE'])) if not str(i) == str(rule_idx)]
                config['DATA_IGNORE_PROPERTY_GARBAGE'] = [config['DATA_IGNORE_PROPERTY_GARBAGE'][i] for i in range(len(config['DATA_IGNORE_PROPERTY_GARBAGE'])) if not str(i) == str(rule_idx)]
        else:
            if 'DATA_SELECT_GARBAGE' not in config:
                config['DATA_SELECT_GARBAGE'] = []
            else:
                config['DATA_SELECT_GARBAGE'] = [config['DATA_SELECT_GARBAGE'][i] for i in range(len(config['DATA_SELECT_GARBAGE'])) if not str(i) == str(rule_idx)]
                config['DATA_SELECT_PROPERTY_GARBAGE'] = [config['DATA_SELECT_PROPERTY_GARBAGE'][i] for i in range(len(config['DATA_SELECT_PROPERTY_GARBAGE'])) if not str(i) == str(rule_idx)]
    save_config(config, config_name)
    return redirect('/param_adjust')

@app.route("/del_rename/<rule_idx>", methods=['GET'])
@require_login(source_name='del_rename', allow_guest=True)
def del_rename(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    rename_rule = [(k, v) for k, v in rename_rule.items()]
    rename_rule = sorted(rename_rule, key=lambda x: x[0])
    rename_rule = [rename_rule[i] for i in range(len(rename_rule)) if not str(i) == str(rule_idx)]
    config['SHORT_NAME_FROM_CONFIG'] = {k: v for k, v in rename_rule}
    save_config(config, config_name)
    return redirect('/param_adjust')



@app.route("/ignore_with_renamed/<rule_idx>", methods=['GET'])
@require_login(source_name='ignore_with_renamed', allow_guest=True)
def ignore_with_renamed(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    rename_rule = [(k, v) for k, v in rename_rule.items()]
    rename_rule = sorted(rename_rule, key=lambda x: x[0])
    selected_value = rename_rule[int(rule_idx)][0]
    if 'DATA_IGNORE' not in config:
        config['DATA_IGNORE'] = []
    newly_added_ignore = {'__SHORT_NAME__': selected_value}
    config['DATA_IGNORE'].append(newly_added_ignore)
    # config['SHORT_NAME_FROM_CONFIG'] = {k: v for k, v in rename_rule}
    save_config(config, config_name)
    return redirect('/param_adjust')



@app.route("/change_plot_order/<alg_name>/<idx>/<method>", methods=['GET'])
@require_login(source_name='change_plot_order', allow_guest=True)
def change_plot_order(alg_name, idx, method):
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if 'PLOTTING_ORDER' not in config:
        config['PLOTTING_ORDER'] = []
    orders = config['PLOTTING_ORDER']
    if not str(idx) == 'None':
        alg_name = base64.urlsafe_b64decode(alg_name.encode()).decode()
        idx = int(idx)
    Logger.logger(f'operate {alg_name} with operator {method}, idx: {idx}')
    if method == 'remove_all':
        orders = []
    elif alg_name == 'placeholder':
        if method == 'top':
            orders = [alg_name] + orders
        elif method == 'down':
            orders = orders + [alg_name]
        elif method == 'up_once':
            if idx > 0:
                tmp = orders[idx-1]
                orders[idx-1] = orders[idx]
                orders[idx] = tmp
        elif method == 'down_once':
            if idx < len(orders) - 1:
                tmp = orders[idx + 1]
                orders[idx + 1] = orders[idx]
                orders[idx] = tmp
        elif method == 'remove':
            orders.pop(int(idx))
    else:
        alg_in_current = alg_name in orders
        if method == 'top':
            if not alg_in_current:
                orders = [alg_name] + orders
            else:
                orders = [item for item in orders if not item == alg_name]
                orders = [alg_name] + orders
        elif method == 'down':
            if not alg_in_current:
                orders = orders + [alg_name]
            else:
                orders = [item for item in orders if not item == alg_name]
                orders = orders + [alg_name]
        elif method == 'remove':
            orders = [item for item in orders if not item == alg_name]
        elif method == 'up_once':
            if idx > 0:
                tmp = orders[idx-1]
                orders[idx-1] = orders[idx]
                orders[idx] = tmp
        elif method == 'down_once':
            if idx < len(orders) - 1:
                tmp = orders[idx + 1]
                orders[idx + 1] = orders[idx]
                orders[idx] = tmp
        else:
            raise NotImplementedError(f'{method} has not been implemented!')
    config['PLOTTING_ORDER'] = orders
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/change_legend_order/<alg_name>/<idx>/<method>", methods=['GET'])
@require_login(source_name='change_legend_order', allow_guest=True)
def change_legend_order(alg_name, idx, method):
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if 'LEGEND_ORDER' not in config:
        config['LEGEND_ORDER'] = []
    orders = config['LEGEND_ORDER']
    if not idx == 'None':
        alg_name = base64.urlsafe_b64decode(alg_name.encode()).decode()
        idx = int(idx)
    Logger.logger(f'operate {alg_name} with operator {method}, idx: {idx}')
    if method == 'remove_all':
        orders = []
    else:
        alg_in_current = alg_name in orders
        if method == 'top':
            if not alg_in_current:
                orders = [alg_name] + orders
            else:
                orders = [item for item in orders if not item == alg_name]
                orders = [alg_name] + orders
        elif method == 'down':
            if not alg_in_current:
                orders = orders + [alg_name]
            else:
                orders = [item for item in orders if not item == alg_name]
                orders = orders + [alg_name]
        elif method == 'remove':
            orders = [item for item in orders if not item == alg_name]
        elif method == 'up_once':
            if idx > 0:
                tmp = orders[idx-1]
                orders[idx-1] = orders[idx]
                orders[idx] = tmp
        elif method == 'down_once':
            if idx < len(orders) - 1:
                tmp = orders[idx + 1]
                orders[idx + 1] = orders[idx]
                orders[idx] = tmp
        else:
            raise NotImplementedError(f'{method} has not been implemented!')
    config['LEGEND_ORDER'] = orders
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/ignore_with_unnamed/<rule_idx>", methods=['GET'])
@require_login(source_name='ignore_with_unnamed', allow_guest=True)
def ignore_with_unnamed(rule_idx):
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    data_ignore = [] if 'DATA_IGNORE' not in config else config['DATA_IGNORE']
    data_select = [] if 'DATA_SELECT' not in config else config['DATA_SELECT']
    data_merge = [] if 'DATA_MERGER' not in config else config['DATA_MERGER']
    data_ignore_property = [] if 'DATA_IGNORE_PROPERTY' not in config else config['DATA_IGNORE_PROPERTY']
    data_select_property = [] if 'DATA_SELECT_PROPERTY' not in config else config['DATA_SELECT_PROPERTY']

    data_short_name_dict = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    data_short_name_property = {} if 'SHORT_NAME_FROM_CONFIG_PROPERTY' not in config else config['SHORT_NAME_FROM_CONFIG_PROPERTY']
    _, _, _, _, _, _, _, _, _, _, short_name_to_ind, _ = analyze_experiment(
        need_ignore=config['USE_IGNORE_RULE'], data_ignore=data_ignore,
        need_select=not config['USE_IGNORE_RULE'], data_select=data_select,
        data_merge=data_merge, data_short_name_dict=data_short_name_dict, data_select_property=data_select_property,
        data_ignore_property=data_ignore_property, data_short_name_property=data_short_name_property)
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    standardize_rule = standardize_merger_item(rename_rule)
    possible_short_name = sorted([k for k in short_name_to_ind if standardize_merger_item(k) not in standardize_rule])
    selected_value = possible_short_name[int(rule_idx)]
    if 'DATA_IGNORE' not in config:
        config['DATA_IGNORE'] = []
    newly_added_ignore = {'__SHORT_NAME__': selected_value}
    config['DATA_IGNORE'].append(newly_added_ignore)
    # config['SHORT_NAME_FROM_CONFIG'] = {k: v for k, v in rename_rule}
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/add_rename", methods=['POST'])
@require_login(source_name='add_rename', allow_guest=True)
def add_rename():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    rename_rule[request.form['added_rule_rename_long']] = request.form['added_rule_rename_short']
    config['SHORT_NAME_FROM_CONFIG'] = rename_rule
    config['SHORT_NAME_FROM_CONFIG_PROPERTY'][request.form['added_rule_rename_long']] = {'manual': 'change_mannual_rename' in request.form}
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/add_data_rename", methods=['POST'])
@require_login(source_name='add_data_rename', allow_guest=True)
def add_data_rename():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    rename_rule = {} if 'DATA_KEY_RENAME_CONFIG' not in config else config['DATA_KEY_RENAME_CONFIG']
    rename_rule[request.form['rename_data_rule']] = request.form['rename_data_new_rule']
    config['DATA_KEY_RENAME_CONFIG'] = rename_rule
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/del_data_rename/<rule_idx>", methods=['GET'])
@require_login(source_name='del_data_rename', allow_guest=True)
def del_data_rename(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    rename_rule = {} if 'DATA_KEY_RENAME_CONFIG' not in config else config['DATA_KEY_RENAME_CONFIG']
    rename_rule = [(k, v) for k, v in rename_rule.items()]
    rename_rule = sorted(rename_rule, key=lambda x: x[0])
    rename_rule = [rename_rule[i] for i in range(len(rename_rule)) if not str(i) == str(rule_idx)]
    config['DATA_KEY_RENAME_CONFIG'] = {k: v for k, v in rename_rule}
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/del_xy/<rule_idx>", methods=['GET'])
@require_login(source_name='del_xy', allow_guest=True)
def del_xy(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if 'PLOTTING_XY' not in config:
        config['PLOTTING_XY'] = []
    else:
        config['PLOTTING_XY'] = [config['PLOTTING_XY'][i] for i in range(len(config['PLOTTING_XY'])) if not str(i) == str(rule_idx)]
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/add_xy", methods=['POST'])
@require_login(source_name='add_xy', allow_guest=True)
def add_xy():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    xy_list = [] if 'PLOTTING_XY' not in config else config['PLOTTING_XY']
    xy_list.append([request.form['x_name'], request.form['y_name']])
    config['PLOTTING_XY'] = xy_list
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/change_filter_rule", methods=['POST'])
@require_login(source_name='change_filter_rule', allow_guest=True)
def change_filter_rule():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if 'filter_data_with_ignore' in request.form:
        config['USE_IGNORE_RULE'] = True
    else:
        config['USE_IGNORE_RULE'] = False
    save_config(config, config_name)
    return redirect('/param_adjust')

@app.route("/change_table_bold_rule", methods=['POST'])
@require_login(source_name='change_table_bold_rule', allow_guest=True)
def change_table_bold_rule():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if 'table_bold_rule' in request.form:
        config['TABLE_BOLD_MAX'] = True
    else:
        config['TABLE_BOLD_MAX'] = False
    save_config(config, config_name)
    return redirect('/table')


@app.route("/del_separator/<rule_idx>", methods=['GET'])
@require_login(source_name='del_separator', allow_guest=True)
def del_separator(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    if 'FIGURE_SEPARATION' not in config:
        config['FIGURE_SEPARATION'] = []
    else:
        if len(config['FIGURE_SEPARATION']) > 1:
            config['FIGURE_SEPARATION'] = [config['FIGURE_SEPARATION'][i] for i in range(len(config['FIGURE_SEPARATION'])) if not str(i) == str(rule_idx)]
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/add_separator", methods=['POST'])
@require_login(source_name='add_separator', allow_guest=True)
def add_separator():
    config_name = query_cookie('used_config')
    config = load_config(config_name)
    separators = [] if 'FIGURE_SEPARATION' not in config else config['FIGURE_SEPARATION']
    separators.append(request.form['separator_item'])
    config['FIGURE_SEPARATION'] = separators
    save_config(config, config_name)
    return redirect('/param_adjust')


# 持续flush
def flush_loop():
    while True:
        sys.stdout.flush()
        time.sleep(1)


def start_page_server(port_num=None):
    Logger.init_global_logger(base_path=page_config.WEB_RAM_PATH, log_name="web_logs")
    _default_config = default_config()
    for k in _default_config:
        if hasattr(plot_config, k):
            _default_config[k] = getattr(plot_config, k)
    save_config(_default_config, 'default_config.json')
    flush_th = threading.Thread(target=flush_loop)
    flush_th.start()
    port_num = port_num if port_num is not None else page_config.PORT
    Logger.logger(f'copy http://{page_config.WEB_NAME}:{port_num} to the explorer')
    if not page_config.REQUIRE_RELOGIN:
        page_config.COOKIE_PERIOD = 1000000
    app.run(host='0', port=port_num, debug=False)


if __name__ == '__main__':
    start_page_server()