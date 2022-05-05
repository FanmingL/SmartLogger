import os

from parameter.Parameter import Parameter
from smart_logger.util_logger.logger import Logger


def main():
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
        logger.sync_log_to_remote()


if __name__ == '__main__':
    main()

