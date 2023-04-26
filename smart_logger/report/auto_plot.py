import os
import time

from smart_logger.common import plot_config
from smart_logger.util_logger.logger import Logger


def system(cmd):
    Logger.local_log(cmd)
    os.system(cmd)


def auto_plot():
    while True:
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            system(f'cd {base_path} && python smart_logger/report/plotting.py')
            if plot_config.FIGURE_SERVER_MACHINE_PASSWD is None:
                for file in plot_config.FIGURE_TO_SYNC:
                    system(
                        f'scp -P {plot_config.FIGURE_SERVER_MACHINE_PORT} -r {os.path.join(plot_config.PLOT_FIGURE_SAVING_PATH, file)}'
                        f' {plot_config.FIGURE_SERVER_MACHINE_USER}@{plot_config.FIGURE_SERVER_MACHINE_IP}:{plot_config.FIGURE_SERVER_MACHINE_TARGET_PATH}')
        except Exception as e:
            Logger.local_log(f'ploting failed, because: {e}')
        time.sleep(60 * 10)


if __name__ == '__main__':
    auto_plot()
