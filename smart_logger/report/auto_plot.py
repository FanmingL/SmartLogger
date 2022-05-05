import os
import time
import os
from smart_logger.report.plotting import plot
from smart_logger.common.plot_config import FIGURE_SERVER_MACHINE_PASSWD, FIGURE_SERVER_MACHINE_USER, \
    FIGURE_SERVER_MACHINE_PORT, FIGURE_SERVER_MACHINE_TARGET_PATH, PLOT_FIGURE_SAVING_PATH, FIGURE_TO_SYNC, \
    FIGURE_SERVER_MACHINE_IP


def system(cmd):
    print(cmd)
    os.system(cmd)


def auto_plot():
    while True:
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            system(f'cd {base_path} && python smart_logger/report/plotting.py')
            if FIGURE_SERVER_MACHINE_PASSWD is None:
                for file in FIGURE_TO_SYNC:
                    system(f'scp -P {FIGURE_SERVER_MACHINE_PORT} -r {os.path.join(PLOT_FIGURE_SAVING_PATH, file)}'
                           f' {FIGURE_SERVER_MACHINE_USER}@{FIGURE_SERVER_MACHINE_IP}:{FIGURE_SERVER_MACHINE_TARGET_PATH}')
        except Exception as e:
            print(f'ploting failed, because: {e}')
        time.sleep(60 * 10)




if __name__ == '__main__':
    auto_plot()
