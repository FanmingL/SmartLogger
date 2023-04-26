import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from demo_parameter.Parameter import Parameter
from smart_logger.util_logger.logger import Logger
import random


def main():
    parameter = Parameter()
    logger = Logger(log_name=parameter.short_name, log_signature=parameter.signature)
    parameter.set_logger(logger)
    parameter.set_config_path(os.path.join(logger.output_dir, 'config'))
    parameter.save_config()
    print(f'parameter: {parameter}')
    for t in range(10):
        logger.log_tabular('timestep', t * 1000, tb_prefix='performance')
        logger.log_tabular('performance', random.random(), tb_prefix='performance')
        logger.add_tabular_data(tb_prefix='test', k1=100, k2=[1, 2, 3, 4, 5], k3=1.23)
        logger.add_tabular_data(tb_prefix='test', k1=1880, k2=2, k3=1.73)
        logger.dump_tabular()


if __name__ == '__main__':
    main()
