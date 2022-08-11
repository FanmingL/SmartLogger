import os
from smart_logger.scripts.generate_tmuxp_base import generate_tmuxp_file, make_cmd_array
import argparse
MAX_SUBWINDOW = 6
MAX_PARALLEL = 10


def get_cmd_array(total_machine=8, machine_idx=0):
    """
    :return: cmd array: list[list[]], the item in the i-th row, j-th column of the return value denotes the
                        cmd in the i-th window and j-th sub-window
    """
    session_name = 'TEST_SESSION'
    # 0. 代码运行路径
    current_path = os.path.dirname(os.path.abspath(__file__))
    # 1. GPU设置
    GPUS = ["\"\""]
    # 2. 环境变量设置
    environment_dict = dict(
        CUDA_VISIBLE_DEVICES="\"\"",
        PYTHONPATH=current_path,
        OMP_NUM_THREADS=1
    )
    directory = current_path
    # 3. 启动脚本
    start_up_header = "python main_logger_and_parameter.py "
    # 4. 基础参数
    parameters_base = dict(
        backing_log=True,
        seed=1
    )
    # 5. 遍历设置
    exclusive_candidates = dict(
        env_name=['HalfCheetah-v2', 'Hopper-v2', 'Ant-v2', 'Walker2d-v2'],
        seed=[13, 17, 23, 31],
        policy_lr=[1e-4, 3e-4, 5e-5]
    )
    # 6. 单独设置
    aligned_candidates = dict(
        information=['value_lr1', 'value_lr2', 'value_lr3'],
        value_lr=[1e-3, 1e-4, 1e-5]
    )

    def task_is_valid(_task):
        return True
    # 从这里开始不用再修改了

    cmd_array, session_name = make_cmd_array(
        directory, session_name, start_up_header, parameters_base, environment_dict,
        aligned_candidates, exclusive_candidates, GPUS, MAX_PARALLEL, MAX_SUBWINDOW,
        machine_idx, total_machine, task_is_valid, split_all=True, sleep_before=0.0, sleep_after=0.0
    )

    for win_ind, win_cmds_list in enumerate(cmd_array):
        for pane_ind, pand_cmd in enumerate(win_cmds_list):
            print(f'win: {win_ind}, pane: {pane_ind}: {pand_cmd}')
    return cmd_array, session_name


def main():
    parser = argparse.ArgumentParser(description=f'generate parallel environment')

    parser.add_argument('--machine_idx', '-idx', type=int, default=-1,
                        help="Server port")
    parser.add_argument('--total_machine_num', '-tn', type=int, default=8,
                        help="Server port")
    args = parser.parse_args()
    cmd_array, session_name = get_cmd_array(args.total_machine_num, args.machine_idx)
    generate_tmuxp_file(session_name, cmd_array, use_json=True)


if __name__ == '__main__':
    main()
