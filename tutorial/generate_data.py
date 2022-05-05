from parameter.Parameter import Parameter
from smart_logger.util_logger.logger import Logger
import random
import os


def generate_data(env_name, seed, policy_lr, information):
    # 模拟一次在环境env_name中，用seed种子跑的实验
    parameter = Parameter()
    parameter.env_name = env_name
    parameter.seed = seed
    parameter.policy_lr = policy_lr
    parameter.information = information
    logger = Logger(log_name=parameter.short_name, log_signature=parameter.signature)
    parameter.set_logger(logger)
    parameter.set_config_path(os.path.join(logger.output_dir, 'config'))
    parameter.save_config()
    print(f'parameter: {parameter}')
    perf = 0
    perf2 = 0
    for t in range(500):
        perf = policy_lr * random.gauss(0.1, 0.4) + perf
        perf2 = policy_lr * random.gauss(0.3, 0.4) + perf2
        logger.log_tabular('timestep', t * 1000, tb_prefix='performance')
        logger.log_tabular('performance', perf, tb_prefix='performance')
        logger.log_tabular('evaluation', perf2, tb_prefix='performance')
        logger.add_tabular_data(tb_prefix='test', k1=100, k2=[1, 2, 3, 4, 5], k3=1.23)
        logger.add_tabular_data(tb_prefix='test', k1=1880, k2=2, k3=1.73)
        logger.dump_tabular()
    return logger.output_dir


def simulate_experiment():
    env_list = ['Hopper-v2', 'HalfCheetah-v2', 'Ant-v2']
    seed_list = [1, 2, 3]
    policy_lr = [0.1, 0.01, 0.001]
    logger_output_dir_list = []
    # 假设我们对三种不同的学习率进行测试，每个学习率在三个环境下分别跑三个不同的种子，大概会使用30秒钟左右的时间来生成数据
    for env in env_list:
        for seed in seed_list:
            for plr in policy_lr:
                log_output_dir = generate_data(env, seed, plr, 'test_for_plot')
                logger_output_dir_list.append(log_output_dir)
    return logger_output_dir_list
