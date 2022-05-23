import random
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, redirect, url_for, request, send_from_directory, send_file, render_template, make_response
import smart_logger.common.page_config as page_config
from smart_logger.util_logger.logger import Logger
import smart_logger.common.plot_config as plot_config
from smart_logger.front_page.experiment_data_loader import default_config, load_config, list_current_experiment, \
    get_parameter, reformat_dict, reformat_str, legal_path, save_config, list_current_configs,\
    make_config_type, analyze_experiment, delete_config_file, has_config, standardize_merger_item, get_record_data_item,\
    get_config_path
from smart_logger.report.plotting import plot as local_plot
from smart_logger.report.plotting import _overwrite_config
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
    if 'name' not in user_data and 'user_name' in request.cookies:
        user_data['name'] = request.cookies['user_name']
    return user_data


def check_user(user_data, allow_guest=False):
    Logger.logger(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: check user {user_data}')
    if 'user_name' in request.cookies and 'cookie_code' in request.cookies and 'used_config' in request.cookies:
        if not has_config(request.cookies['used_config']):
            return False
        _user_name = request.cookies['user_name']
        _code = request.cookies['cookie_code']
        if 'name' not in user_data or not user_data['name'] == _user_name:
            user_data['name'] = _user_name
        return True
    else:
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
    # result = len(user_data['nm']) > 0 and len(user_data['passwd']) > 0
    user_name = user_data['nm']

    if result:
        source_page = user_data['from'] if 'from' in user_data else None
        if source_page is not None and len(source_page) > 0:
            target_page = source_page
        else:
            target_page = 'experiment'
        Logger.logger(f'redirect to {target_page}')
        outdate = datetime.now() + timedelta(hours=2)
        response = make_response(redirect(target_page))
        response.set_cookie('user_name', user_name, expires=outdate)
        code = generate_code(20)
        response.set_cookie('cookie_code', code, expires=outdate)
        if load_config('default_config.json') is None:
            save_config(default_config(), 'default_config.json')
        outdate_config_path = datetime.now() + timedelta(hours=10)
        candidate_config = []
        for item in list_current_configs():
            candidate_config.append(item)
        Logger.logger(f'found configs: {candidate_config}')
        if len(candidate_config) == 0:
            config = load_config('default_config.json')
            config_name = 'config-{}-{}-{}.json'.format(user_name,
                                                        datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), generate_code(10))
            save_config(config, config_name)
        else:
            config_name = candidate_config[-1]
            config = load_config(config_name)
            if config is None:
                config = load_config('default_config.json')
                config_name = 'config-{}-{}-{}.json'.format(request.cookies['user_name'],
                                                            datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                                                            generate_code(10))
                save_config(config, config_name)
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
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    _overwrite_config(config)
    exp_folders = list_current_experiment()
    exp_folders_code = [base64.urlsafe_b64encode(item.encode()).decode() for item in exp_folders]
    return render_template('t_experiment.html', exp_folder_list=exp_folders, exp_folders_code=exp_folders_code)


@app.route("/experiment_parameter/<folder_name>", methods=['GET'])
@require_login(source_name='experiment_parameter', allow_guest=True)
def obtain_experiment_parameter(folder_name):
    folder_name = base64.urlsafe_b64decode(folder_name.encode()).decode()
    # return "Hello World"
    param, dtree, full_path, name, filesize, important_configs = get_parameter(folder_name)
    for i in range(len(full_path)):
        if full_path[i] is not None:
            full_path[i] = base64.urlsafe_b64encode(os.path.join(os.path.dirname(folder_name), full_path[i]).encode()).decode()
        else:
            full_path[i] = 'None'
    if param is None:
        return render_template('404.html')
    dtree_desc = reformat_str(dtree)
    param_desc = reformat_dict(param)
    important_configs = reformat_dict(important_configs)
    recorded_data = get_record_data_item(folder_name)

    return render_template('t_parameter_display.html',
                           experiment_description=param_desc,
                           dtree_desc=dtree_desc,
                           name=folder_name,
                           full_path=full_path,
                           filenames=name,
                           important_configs=important_configs,
                           filesize=filesize,
                           recorded_data=recorded_data)


@app.route("/experiment_data_download/<folder_name>", methods=['GET'])
@require_login(source_name='experiment_data_download', allow_guest=True)
def experiment_data_download(folder_name):
    # return "Hello World"
    folder_name = base64.urlsafe_b64decode(folder_name.encode()).decode()
    file_name = os.path.join(plot_config.PLOT_LOG_PATH, folder_name)
    if not legal_path(file_name):
        Logger.logger(f'file {file_name} is not legal')
        return render_template('404.html')
    if os.path.exists(file_name):
        Logger.logger(f'file {file_name} exists')
        filename = os.path.basename(file_name)
        dirname = os.path.dirname(file_name)
        as_attachment = True if not (
                    filename.lower().endswith('png') or filename.lower().endswith('jpg') or filename.lower().endswith(
                'txt') or filename.lower().endswith('json')) else False
        return send_from_directory(dirname, filename, as_attachment=as_attachment)

    else:
        Logger.logger(f'file {file_name} does not exist')
        return render_template('404.html')


@app.route("/plot", methods=['GET'])
@require_login(source_name='plot', allow_guest=True)
def plot():
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    config = {k: v for k, v in config.items() if k not in ['SHORT_NAME_FROM_CONFIG', 'DATA_IGNORE', 'DATA_MERGER',
                                                           'PLOTTING_XY', 'FIGURE_TO_SYNC', 'FIGURE_SEPARATION',
                                                           'DATA_KEY_RENAME_CONFIG', 'DESCRIPTION',
                                                           'LOG_DIR_BACKING_NAME', 'DATA_PATH',
                                                           'PLOT_FIGURE_SAVING_PATH', 'FIGURE_SERVER_MACHINE_IP',
                                                           'FIGURE_SERVER_MACHINE_PORT', 'FIGURE_SERVER_MACHINE_USER',
                                                           'FIGURE_SERVER_MACHINE_PASSWD',
                                                           'FIGURE_SERVER_MACHINE_TARGET_PATH', 'PLOTTING_ORDER']}
    config_description = plot_config.DESCRIPTION
    for k in config:
        if k not in config_description:
            config_description[k] = 'None'
    config_type = make_config_type(config)
    return render_template('t_plot.html',
                             plot_config=config,   # plot_config list list
                           config_type=config_type,
                             config_name=config_name,
                           description=config_description)


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
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
    if config_name.endswith('.json'):
        output_path = os.path.join(page_config.FIGURE_PATH, request.cookies['user_name'], config_name[:-5])
    else:
        output_path = os.path.join(page_config.FIGURE_PATH, request.cookies['user_name'], config_name)
    config = load_config(config_name)
    config['PLOT_FIGURE_SAVING_PATH'] = output_path
    save_config(config, config_name)
    config_path = get_config_path(config_name)
    Logger.logger(f'plot figure according to {config_path}, figure save to {output_path}')
    local_plot(config_path)
    saving_png = f'{os.path.join(output_path, plot_config.FINAL_OUTPUT_NAME)}.png'
    Logger.logger(f'return figure {saving_png}, drawing cost {time.time() - start_time}')
    target_folder = os.path.join(page_config.WEB_RAM_PATH, page_config.TOTAL_FIGURE_FOLDER, f'{plot_config.FINAL_OUTPUT_NAME}.png')

    Logger.logger(f'cp {saving_png} {target_folder}')
    os.makedirs(os.path.dirname(target_folder), exist_ok=True)
    os.system(f'cp {saving_png} {target_folder}')
    return send_from_directory(output_path, f'{plot_config.FINAL_OUTPUT_NAME}.png', as_attachment=False)


@app.route("/param_adjust", methods=['GET'])
@require_login(source_name='param_adjust', allow_guest=True)
def param_adjust():
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    _overwrite_config(config)
    data_ignore = {} if 'DATA_IGNORE' not in config else config['DATA_IGNORE']
    data_merge = [] if 'DATA_MERGER' not in config else config['DATA_MERGER']
    data_short_name_dict = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    exp_data, exp_data_ignores, selected_choices, alg_idx, possible_config, short_name_to_ind, nick_name_list = analyze_experiment(need_ignore=True, data_ignore=data_ignore,
                                                                      data_merge=data_merge, data_short_name_dict=data_short_name_dict)
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
    merge_config_file = [(k, v[0], v[1]) for k, v in merge_config_file.items()]
    merge_config_file = list(reversed(sorted(sorted(merge_config_file, key=lambda x: x[1]), key=lambda x: x[2])))
    possible_config = [(k, v) for k, v in possible_config.items()]
    possible_config = [*reversed(sorted(possible_config, key=lambda x: len(x[1])))]
    # Logger.logger(f'possible config json: {json.dumps(possible_config)}')
    encode_possible_config_js = base64.urlsafe_b64encode(json.dumps(possible_config).encode()).decode()
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    rename_rule_dict = rename_rule
    standardize_rule = standardize_merger_item(rename_rule)
    possible_short_name = sorted([k for k in short_name_to_ind if standardize_merger_item(k) not in standardize_rule])
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
    return render_template('t_param_adapt.html',
                           exp_data=exp_data,
                           exp_data_encoded=exp_data_encoded,
                           exp_data_ignores=exp_data_ignores,
                           exp_data_ignores_encoded=exp_data_ignores_encoded,
                           selected_choices=selected_choices,
                           merge_config_file=merge_config_file,  # merge_config_file list list
                           alg_idx=alg_idx,
                           data_ignore=data_ignore,  # data_ignore list list
                           rename_rule_dict=rename_rule_dict,
                           possible_config=possible_config,
                           possible_config_js=encode_possible_config_js,
                           rename_rule=rename_rule,  # rename_rule list list
                           plotting_xy=plotting_xy,  # plotting_xy list list
                           possible_short_name=possible_short_name,
                           nick_name_list=nick_name_list,
                           config_file_list=config_file_list,
                           config_name=config_name,
                           rename_rule_data=rename_rule_data,
                           separators=separators,
                           exists_ordered_curves=exists_ordered_curves,
                           remain_unordered_curves=remain_unordered_curves,
                           exists_ordered_curves_encode=exists_ordered_curves_encode,
                           remain_unordered_curves_encode=remain_unordered_curves_encode
                           )



@app.route("/merge_process", methods=['POST'])
@require_login(source_name='merge_process', allow_guest=True)
def merge_process():
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    new_merger = [k for k in request.form]
    config['DATA_MERGER'] = new_merger
    save_config(config, config_name)
    return redirect('param_adjust')

def _choose_config(config_name):
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
    if k_set_mismatch:
        save_config(config_new, config_name)

@app.route("/choose_config", methods=['POST'])
@require_login(source_name='choose_config', allow_guest=True)
def choose_config():
    response = make_response(redirect('param_adjust'))
    outdate_config_path = datetime.now() + timedelta(hours=10)
    config_name = request.form.get('chosen_config', None)
    if config_name is not None:
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
    _choose_config(config_name)
    return response

@app.route("/rename_config", methods=['POST'])
@require_login(source_name='rename_config', allow_guest=True)
def rename_config():
    response = make_response(redirect('param_adjust'))
    config_name = request.cookies['used_config']
    config_name_legacy = config_name
    config = load_config(config_name)
    outdate_config_path = datetime.now() + timedelta(hours=10)
    config_name = request.form.get('rename', None)
    if config_name is not None and len(config_name) > 0:
        delete_config_file(config_name_legacy)
        save_config(config, config_name)
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
    return response

@app.route("/create_config", methods=['GET'])
@require_login(source_name='create_config', allow_guest=True)
def create_config():
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    config_name = 'config-{}-{}-{}.json'.format(request.cookies['user_name'],
                                                datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                                                generate_code(10))
    save_config(config, config_name)
    response = make_response(redirect('param_adjust'))
    outdate_config_path = datetime.now() + timedelta(hours=10)
    response.set_cookie('used_config', config_name, expires=outdate_config_path)
    return response


@app.route("/delete_config", methods=['POST'])
@require_login(source_name='delete_config', allow_guest=True)
def delete_config():
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    delete_file = json.loads(request.data.decode())['delete_config']
    delete_config_file(delete_file)
    response = make_response(redirect('param_adjust'))

    if delete_file == config_name:
        config_list = list_current_configs()
        if len(config_list) == 0:
            config_name = 'config-{}-{}-{}.json'.format(request.cookies['user_name'],
                                                        datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                                                        generate_code(10))

            save_config(config, config_name)
        else:
            config_name = config_list[-1]
        outdate_config_path = datetime.now() + timedelta(hours=10)
        response.set_cookie('used_config', config_name, expires=outdate_config_path)
    return response

@app.route("/reset_config", methods=['GET'])
@require_login(source_name='reset_config', allow_guest=True)
def reset_config():
    config = load_config('default_config.json')
    if config is None:
        config = default_config()
    config_name = request.cookies['used_config']
    save_config(config, config_name)
    return redirect('param_adjust')


@app.route("/merge_config", methods=['POST'])
@require_login(source_name='merge_config', allow_guest=True)
def merge_config():
    config_target = load_config(request.form['target_config'])
    if config_target is None:
        config_target = default_config()
    config_name = request.cookies['used_config']
    config_current = load_config(config_name)
    for k in config_current:
        if k in config_target:
            config_current[k] = config_target[k]
    for k in config_target:
        if k not in config_current:
            config_current[k] = config_target[k]
    save_config(config_current, config_name)
    return redirect('param_adjust')

@app.route("/add_ignore", methods=['POST'])
@require_login(source_name='add_ignore', allow_guest=True)
def add_ignore():
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    newly_added_ignore = json.loads(request.data.decode())
    if 'DATA_IGNORE' not in config:
        config['DATA_IGNORE'] = []
    if len(newly_added_ignore) > 0:
        config['DATA_IGNORE'].append(newly_added_ignore)
    save_config(config, config_name)
    return redirect('param_adjust')


@app.route("/del_ignore/<rule_idx>", methods=['GET'])
@require_login(source_name='del_ignore', allow_guest=True)
def del_ignore(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    if 'DATA_IGNORE' not in config:
        config['DATA_IGNORE'] = []
    else:
        config['DATA_IGNORE'] = [config['DATA_IGNORE'][i] for i in range(len(config['DATA_IGNORE'])) if not str(i) == str(rule_idx)]
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/del_rename/<rule_idx>", methods=['GET'])
@require_login(source_name='del_rename', allow_guest=True)
def del_rename(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
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


@app.route("/ignore_with_unnamed/<rule_idx>", methods=['GET'])
@require_login(source_name='ignore_with_unnamed', allow_guest=True)
def ignore_with_unnamed(rule_idx):
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    data_ignore = {} if 'DATA_IGNORE' not in config else config['DATA_IGNORE']
    data_merge = [] if 'DATA_MERGER' not in config else config['DATA_MERGER']
    data_short_name_dict = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    _, _, _, _, _, short_name_to_ind, _ = analyze_experiment(
        need_ignore=True, data_ignore=data_ignore,
        data_merge=data_merge, data_short_name_dict=data_short_name_dict)
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
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    rename_rule = {} if 'SHORT_NAME_FROM_CONFIG' not in config else config['SHORT_NAME_FROM_CONFIG']
    rename_rule[request.form['added_rule_rename_long']] = request.form['added_rule_rename_short']
    config['SHORT_NAME_FROM_CONFIG'] = rename_rule
    save_config(config, config_name)
    return redirect('/param_adjust')


@app.route("/add_data_rename", methods=['POST'])
@require_login(source_name='add_data_rename', allow_guest=True)
def add_data_rename():
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
    config = load_config(config_name)
    xy_list = [] if 'PLOTTING_XY' not in config else config['PLOTTING_XY']
    xy_list.append([request.form['x_name'], request.form['y_name']])
    config['PLOTTING_XY'] = xy_list
    save_config(config, config_name)
    return redirect('/param_adjust')

@app.route("/del_separator/<rule_idx>", methods=['GET'])
@require_login(source_name='del_separator', allow_guest=True)
def del_separator(rule_idx):
    Logger.logger(f'try to rm {rule_idx} {type(rule_idx)}')
    config_name = request.cookies['used_config']
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
    config_name = request.cookies['used_config']
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
    app.run(host='0', port=port_num, debug=False)


if __name__ == '__main__':
    start_page_server()