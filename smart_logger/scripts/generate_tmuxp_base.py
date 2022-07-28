import copy
import yaml
import os
import math
# 生成run_all.yaml，以并行启动程序
# 用tmuxp load run_all.yaml来一键启动程序
# 可以不用改，主要影响窗体结构
MAX_SUBWINDOW = 6
# 最大允许并行的进程的数量，若指定要运行的进程数大于该值，多余的进程将会在前面的进程完成之后进行（串行进行）
MAX_PARALLEL = 3

def make_cmd(environment_dict: dict, directory: str, start_up_header: str, parameter_dict: dict):
    cmd = ""
    for ind, (k, v) in enumerate(environment_dict.items()):
        if ind == 0:
            cmd += f"export {k}={v} && "
        else:
            cmd += f" export {k}={v} && "
    cmd += f" cd {directory} && "
    cmd += f" {start_up_header} "
    for k, v in parameter_dict.items():
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


def cmd_post_process(cmd):
    return cmd


def check_aligned_valid(_aligned_candidates):
    parallel_task = None
    for k, v in _aligned_candidates.items():
        if isinstance(v, list):
            if parallel_task is None:
                parallel_task = len(v)
            else:
                assert len(v) == parallel_task, f"length of key {k} violates the given length"
    assert parallel_task is not None
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


def get_cmd_array(max_subwindows, max_parallel_process):
    """
    :return: cmd array: list[list[]], the item in the i-th row, j-th column of the return value denotes the
                        cmd in the i-th window and j-th sub-window
    """
    session_name = 'SMARTLOGGER_TEST'
    # 0. 代码运行路径
    # current_path = os.path.dirname(os.path.abspath(__file__))
    current_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'sml_tutorial')
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
    # 从这里开始不用再修改了
    aligned_task_num = check_aligned_valid(aligned_candidates)
    exclusive_keys = list(exclusive_candidates.keys())
    possible_assemble_dicts = _get_all_permutation(dict(), key_list=exclusive_keys,
                                                   key_choices=[exclusive_candidates[k] for k in exclusive_keys])

    final_tasks_list = []
    for exclusive_task in possible_assemble_dicts:
        for ind in range(aligned_task_num):
            task = copy.deepcopy(exclusive_task)
            for k, v in aligned_candidates.items():
                if isinstance(v, list):
                    task[k] = v[ind]
                else:
                    task[k] = v
            final_tasks_list.append(task)
    cmd_list = []
    cmd_num_per_pane = int(math.ceil(len(final_tasks_list) / max_parallel_process))
    total_pane_num = min(max_parallel_process, len(final_tasks_list))
    for pane_ind in range(total_pane_num):
        cmd = ''
        for cmd_ind in range(cmd_num_per_pane):
            task_ind = pane_ind + cmd_ind * total_pane_num
            if task_ind < len(final_tasks_list):
                task = final_tasks_list[task_ind]
                parameters = copy.deepcopy(parameters_base)
                parameters.update(task)
                environment_dict['CUDA_VISIBLE_DEVICES'] = str(GPUS[task_ind % len(GPUS)])
                cmd_once = make_cmd(environment_dict, directory, start_up_header, parameters)
                cmd_once = cmd_post_process(cmd_once)
                if cmd_ind == 0:
                    cmd = cmd_once
                else:
                    cmd = cmd + ' && ' + cmd_once
        cmd_list.append(cmd)
        if len(cmd_list) >= max_subwindows:
            cmd_array.append(cmd_list)
            cmd_list = []
    if len(cmd_list) > 0:
        cmd_array.append(cmd_list)
    if isinstance(aligned_candidates['information'], list):
        session_name += '_'.join(aligned_candidates['information'])
    else:
        session_name += aligned_candidates['information']
    session_name = session_name.replace('.', '_')
    # 上面不用修改了

    # customized command
    # 7. 额外命令
    cmd_array.append(['htop'])
    print('='*30, 'SUMMARIZE', '='*30)
    for win_ind, win_cmds_list in enumerate(cmd_array):
        for pane_ind, pand_cmd in enumerate(win_cmds_list):
            print(f'win: {win_ind}, pane: {pane_ind}: {pand_cmd}')
    print('='*30, 'END', '='*30)

    return cmd_array, session_name


def generate_tmuxp_file(session_name, cmd_array):
    config = {"session_name": session_name, "windows": []}
    for window_ind, cmd_list in enumerate(cmd_array):
        window_cmd = {
            "window_name": f"window-{window_ind}",
            "panes": cmd_list,
            "layout": "tiled"
        }
        config["windows"].append(window_cmd)
    print(f'session name: {config["session_name"]}')
    yaml.dump(config, open("run_all.yaml", "w"), default_flow_style=False)


def main():
    cmd_array, session_name = get_cmd_array(MAX_SUBWINDOW, MAX_PARALLEL)
    generate_tmuxp_file(session_name, cmd_array)


if __name__ == '__main__':
    main()