import os.path
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Process
from multiprocessing import current_process

import smart_logger
import smart_logger.common.common_config as common_config
import smart_logger.common.experiment_config as experiment_config


def single_process(logger_config=None):
    print(f'multi process name: {current_process().name}')
    # if logger_config is not None:
    #     smart_logger.set_total_config(logger_config)
    print(f'customized config: {experiment_config.get_customized_value("abc")}')
    print(f'base path: {common_config.BASE_PATH}')
    import numpy as np
    print('random status', np.random.get_state()[-4][10])


def process_test():
    print('-' * 30, 'process test', '-' * 30)
    phs = [Process(target=single_process, args=(smart_logger.get_total_config(),), ) for _ in range(3)]
    for ph in phs:
        ph.start()
    for ph in phs:
        ph.join()


def process_pool_test():
    print('-' * 30, 'pool test', '-' * 30)
    process_pool = ProcessPoolExecutor(max_workers=1)
    tasks = [smart_logger.get_total_config() for _ in range(5)]
    futures = []
    for _future in process_pool.map(single_process, tasks):
        futures.append(_future)


def main():
    import numpy as np
    np.random.seed(0)

    smart_logger.set_experiment_customized_config(abc=10)
    smart_logger.set_common_config(BASE_PATH=os.path.dirname(__file__))
    single_process()
    process_test()
    process_pool_test()


if __name__ == '__main__':
    main()
