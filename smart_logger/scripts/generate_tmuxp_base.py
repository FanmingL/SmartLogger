import copy
import json
import math
import os
import random

import yaml

# 生成run_all.yaml，以并行启动程序
# 用tmuxp load run_all.yaml来一键启动程序
# 可以不用改，主要影响窗体结构
MAX_SUBWINDOW = 6
# 最大允许并行的进程的数量，若指定要运行的进程数大于该值，多余的进程将会在前面的进程完成之后进行（串行进行）
MAX_PARALLEL = 6
# 任务由几台机器一块完成
MACHINE_NUM = 8
# 当前机器序号ID, -1表示只有一台机器
MACHINE_IDX = -1


def make_cmd(environment_dict: dict, directory: str, start_up_header: str,
             parameter_dict: dict, task_ind: int = -1, total_task_num: int = -1, equality_assign: bool = False):
    cmd = ""
    for ind, (k, v) in enumerate(environment_dict.items()):
        if ind == 0:
            cmd += f"export {k}={v} && "
        else:
            cmd += f" export {k}={v} && "
    cmd += f" cd {directory} && "
    if total_task_num > 0 and task_ind >= 0:
        cmd += f" echo \'******************task ind: {task_ind + 1}/{total_task_num} ************************\' && "
    cmd += f" {start_up_header} "
    for k, v in parameter_dict.items():
        if equality_assign:
            if v is None:
                pass
            elif isinstance(v, bool):
                if v:
                    cmd += f" {k}={v} "
            else:
                cmd += f" {k}={v} "
        else:
            if v is None:
                pass
            elif isinstance(v, bool):
                if v:
                    cmd += f" --{k} "
            elif isinstance(v, list):
                if len(v) > 0:
                    v = [str(item) for item in v]
                    cmd += f" --{k} {' '.join(v)} "
            else:
                cmd += f" --{k} {v} "
    print(cmd)
    return cmd


def _cmd_post_process(cmd):
    return cmd


def check_aligned_valid(_aligned_candidates):
    parallel_task = 1
    for k, v in _aligned_candidates.items():
        if isinstance(v, list):
            if parallel_task is None or parallel_task == 1:
                parallel_task = len(v)
            else:
                if not len(v) == 1:
                    assert len(v) == parallel_task, f"length of key {k} violates the given length"
    return parallel_task


def _get_all_permutation(current_dict, key_list, key_choices):
    if len(key_list) == 0:
        return [current_dict]
    current_key = key_list[0]
    current_choices = key_choices[0]
    key_list = key_list[1:]
    key_choices = key_choices[1:]
    dict_list = []
    for choice in current_choices:
        current_dict = copy.deepcopy(current_dict)
        current_dict[current_key] = choice
        possible_dict_res = _get_all_permutation(current_dict, key_list, key_choices)
        dict_list += possible_dict_res
    return dict_list


def make_cmd_array(directory, session_name, start_up_header,
                   parameters_base, environment_dict, aligned_candidates,
                   exclusive_candidates, GPUS, max_parallel_process, max_subwindow=6,
                   machine_idx=-1, total_machine=8, task_is_valid=None, split_all=False,
                   cmd_post_process=None, sleep_before=0.0, sleep_after=0.0, error_stop=False,
                   rnd_seed=42, equality_assign=False):
    if rnd_seed is not None:
        random_gen = random.Random()
        random_gen.seed(rnd_seed)
    else:
        random_gen = None
    cmd_sep = '&&' if error_stop else ';'
    sub_cmd_sep = ' && '  # ';\\'
    cmd_array = []

    aligned_task_num = check_aligned_valid(aligned_candidates)
    exclusive_keys = list(exclusive_candidates.keys())
    possible_assemble_dicts = _get_all_permutation(dict(), key_list=exclusive_keys,
                                                   key_choices=[exclusive_candidates[k] for k in exclusive_keys])

    final_tasks_list = []
    for exclusive_task in possible_assemble_dicts:
        for ind in range(aligned_task_num):
            task = copy.deepcopy(parameters_base)
            task.update(exclusive_task)
            for k, v in aligned_candidates.items():
                if isinstance(v, list):
                    if len(v) == 1:
                        task[k] = v[0]
                    else:
                        task[k] = v[ind]
                else:
                    task[k] = v
            final_tasks_list.append(task)
    if task_is_valid is not None:
        final_tasks_list = [task for task in final_tasks_list if task_is_valid(task)]
    if random_gen is not None:
        random_gen.shuffle(final_tasks_list)
    cmd_list = []
    total_task_num = len(final_tasks_list)
    if not machine_idx == -1:
        tasks_per_machine = math.ceil(len(final_tasks_list) / total_machine)
        final_tasks_list = final_tasks_list[tasks_per_machine * machine_idx: min(len(final_tasks_list),
                                                                                 tasks_per_machine * (machine_idx + 1))]
    cmd_num_per_pane = int(math.ceil(len(final_tasks_list) / max_parallel_process))
    total_pane_num = min(max_parallel_process, len(final_tasks_list))
    task_ind_list = []
    for pane_ind in range(total_pane_num):
        cmd = ''
        for cmd_ind in range(cmd_num_per_pane):
            # task_ind = cmd_ind + pane_ind * cmd_num_per_pane
            task_ind = pane_ind + cmd_ind * total_pane_num
            if ((cmd_num_per_pane - 1) * total_pane_num + pane_ind + 1) <= len(final_tasks_list):
                total_pane_task_num = cmd_num_per_pane
            else:
                total_pane_task_num = cmd_num_per_pane - 1
            if task_ind < len(final_tasks_list):
                task = final_tasks_list[task_ind]
                task_ind_list.append(task_ind)
                parameters = copy.deepcopy(parameters_base)
                parameters.update(task)
                if 'CUDA_VISIBLE_DEVICES' in environment_dict and len(GPUS) > 0:
                    environment_dict['CUDA_VISIBLE_DEVICES'] = str(GPUS[task_ind % len(GPUS)])
                cmd_once = make_cmd(environment_dict, directory, start_up_header, parameters, cmd_ind,
                                    total_pane_task_num, equality_assign)
                if cmd_post_process is not None:
                    cmd_once = cmd_post_process(cmd_once)
                if cmd_ind == 0:
                    if split_all:
                        cmd = dict(shell_command=cmd_once.split('&&') + [cmd_sep])
                        if sleep_after > 0:
                            cmd['sleep_after'] = sleep_after
                        if sleep_before > 0:
                            cmd['sleep_before'] = sleep_before
                    else:
                        cmd = cmd_once
                else:
                    if split_all:
                        cmd['shell_command'] += cmd_once.split('&&')
                        cmd['shell_command'].append(cmd_sep)
                    else:
                        if isinstance(cmd, dict):
                            cmd['shell_command'].append(cmd_once)
                        else:
                            cmd = dict(shell_command=[cmd_once], sleep_before=sleep_before, sleep_after=sleep_after)
        if split_all:
            if not isinstance(cmd, dict):
                cmd = dict(shell_command=[' echo \' task finished!!! \' && date ', cmd_sep], sleep_before=sleep_before,
                           sleep_after=sleep_after)
            else:
                cmd['shell_command'].append(' echo \' task finished!!! \' && date ')
                cmd['shell_command'].append(cmd_sep)
        else:
            if isinstance(cmd, dict):
                cmd['shell_command'].append(' echo \' task finished!!! \' && date ')
            else:
                cmd = dict(shell_command=[' echo \' task finished!!! \' && date '], sleep_before=sleep_before,
                           sleep_after=sleep_after)
        if split_all:
            for cmd_ind, cmd_item in enumerate(cmd['shell_command']):
                if cmd_ind < len(cmd['shell_command']) - 2:
                    if cmd['shell_command'][cmd_ind + 1] == cmd_sep:
                        cmd['shell_command'][cmd_ind] += f'\\'
                    elif cmd['shell_command'][cmd_ind] == cmd_sep:
                        cmd['shell_command'][cmd_ind] = f'{cmd_sep}\\'
                    else:
                        # cmd['shell_command'][cmd_ind] += ' ;\\'
                        cmd['shell_command'][cmd_ind] += sub_cmd_sep
            cmd['shell_command'] = cmd['shell_command'][:-1]
        cmd_list.append(cmd)
        if len(cmd_list) >= max_subwindow:
            cmd_array.append(cmd_list)
            cmd_list = []
    if len(cmd_list) > 0:
        cmd_array.append(cmd_list)
    if 'information' in aligned_candidates:
        if isinstance(aligned_candidates['information'], list):
            session_name += '_'.join(aligned_candidates['information'])
        else:
            session_name += aligned_candidates['information']
    else:
        pass
    session_name = session_name.replace('.', '_')
    print('*' * 70)
    print(f'Machine num: {1 if machine_idx < 0 else machine_idx}/{1 if machine_idx < 0 else total_machine}, '
          f'Task num: {len(final_tasks_list)}/{total_task_num}, pane num: {total_pane_num}, task per pane: {cmd_num_per_pane}\n'
          f'Task ind: {sorted(task_ind_list)}, task ind len: {len(task_ind_list)}')
    print('*' * 70)
    return cmd_array, session_name


def get_cmd_array(max_subwindows, max_parallel_process, machine_idx, total_machine):
    """
    :return: cmd array: list[list[]], the item in the i-th row, j-th column of the return value denotes the
                        cmd in the i-th window and j-th sub-window
    """
    session_name = 'SMARTLOGGER_TEST'
    # 0. 代码运行路径
    # current_path = os.path.dirname(os.path.abspath(__file__))
    current_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'sml_tutorial')
    cmd_array = []
    # GPUS = [0, 1, 2, 3]
    # 1. GPU设置
    GPUS = ["\"\""]
    # GPUS = [0, 1t, 2, 3]
    # 2. 环境变量设置
    environment_dict = dict(
        CUDA_VISIBLE_DEVICES="\"\"",
        PYTHONPATH=current_path,
        OMP_NUM_THREADS=1
    )
    directory = current_path
    # 3. 启动脚本
    start_up_header = "python basic_log_demo.py "
    # 4. 基础参数
    parameters_base = dict(
        policy_lr=1e-4
    )
    # 5. 遍历设置
    exclusive_candidates = dict(
        env_name=["Hopper-v2", "Ant-v2", "HalfCheetah-v2", "Walker2d-v2"],
        seed=[11, 111, 1111],
    )
    # 6. 单独设置
    aligned_candidates = dict(
        information=['TEST', 'TRAIN'],
        backing_log=[True, False],
        policy_lr=[1e-4, 1e-3],
    )
    cmd_array, session_name = make_cmd_array(
        directory, session_name, start_up_header, parameters_base, environment_dict,
        aligned_candidates, exclusive_candidates, GPUS, max_parallel_process, max_subwindows,
        machine_idx, total_machine, task_is_valid=lambda x: True, cmd_post_process=lambda x: x, equality_assign=True
    )
    # customized command
    # 7. 额外命令
    # cmd_array.append(['htop'])
    print('=' * 30, 'SUMMARIZE', '=' * 30)
    for win_ind, win_cmds_list in enumerate(cmd_array):
        for pane_ind, pand_cmd in enumerate(win_cmds_list):
            print(f'win: {win_ind}, pane: {pane_ind}: {pand_cmd}')
    print('=' * 30, 'END', '=' * 30)

    return cmd_array, session_name


def generate_tmuxp_file(session_name, cmd_array, use_json=False, layout='tiled', window_names=None):
    """
    layout的选项
    even-horizontal：窗口中的面板将均匀地水平排列。
    even-vertical：窗口中的面板将均匀地垂直排列。
    main-horizontal：一个主面板在上，其他面板在下均匀地水平排列。
    main-vertical：一个主面板在左，其他面板在右均匀地垂直排列。
    tiled：面板在窗口中平均地排列。
    """
    if window_names is not None:
        assert len(cmd_array) == len(window_names), f'length of the commands and the window names' \
                                                    f' should be the same, but got cmd len: {len(window_names)} and window len: {len(cmd_array)}'
    config = {"session_name": session_name, "windows": []}
    for window_ind, cmd_list in enumerate(cmd_array):
        window_name = f"window-{window_ind}" if window_names is None else window_names[window_ind]
        window_cmd = {
            "window_name": window_name,
            "panes": cmd_list,
            "layout": layout
        }
        config["windows"].append(window_cmd)
    print(f'session name: {config["session_name"]}')
    if use_json:
        json.dump(config, open('run_all.json', 'w'))
    else:
        yaml.dump(config, open("run_all.yaml", "w"), default_flow_style=False)


def main():
    cmd_array, session_name = get_cmd_array(MAX_SUBWINDOW, MAX_PARALLEL, MACHINE_IDX, MACHINE_NUM, )
    generate_tmuxp_file(session_name, cmd_array)


if __name__ == '__main__':
    main()
