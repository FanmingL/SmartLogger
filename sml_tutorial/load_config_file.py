import os

from demo_parameter.Parameter import Parameter
from smart_logger.util_logger.logger import Logger
from smart_logger.common.serialize_config import init_config


def main():
    init_config(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo_configs', 'common_config.yaml'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo_configs', 'experiment_config.yaml'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logfile_tmp'),
    )
    parameter = Parameter()
    logger = Logger(log_name=parameter.short_name, log_signature=parameter.signature, logger_category=parameter.suffix)
    parameter.set_logger(logger)
    parameter.set_config_path(os.path.join(logger.output_dir, 'config'))
    parameter.save_config()
    print(f'parameter: {parameter}')
    for _ in range(10):
        logger.log_tabular('a', 2)
        logger.log_tabular('b', 1)
        logger.dump_tabular()
        # logger.sync_log_to_remote()


if __name__ == '__main__':
    main()