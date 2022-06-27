import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import smart_logger.common.page_config as page_config
import smart_logger.common.plot_config as plot_config
from smart_logger.front_page.page import start_page_server
from smart_logger.common.set_config import set_page_config, set_plot_config
import argparse


def main():
    parser = argparse.ArgumentParser(description=f'数据可视化服务启动参数配置')

    parser.add_argument('--workspace_path', '-wks', type=str, default='~/Desktop/small_logger_cache',
                        help="Path to the workspace, used to saving cache data")
    parser.add_argument('--data_path', '-d', type=str, default='/full/path/to/data',
                        help="Path to the data")
    parser.add_argument('--user_name', '-u', type=str, default='user',
                        help="user name")
    parser.add_argument('--password', '-pw', type=str, default='123456',
                        help="password")
    parser.add_argument('--port', '-p', type=int, default=7005,
                        help="Server port")
    args = parser.parse_args()
    set_plot_config(
        # 关键配置项1：数据目录，该目录下存有日志文件
        DATA_PATH=args.data_path,
        WORKSPAPCE=os.path.expanduser(args.workspace_path),
        DATA_MERGER=[],
        PLOTTING_XY=[],
        PLOT_LOG_PATH=f"{plot_config.DATA_PATH}",
        PLOT_FIGURE_SAVING_PATH=f"{os.path.join(os.path.dirname(plot_config.DATA_PATH), 'figure')}"
    )

    set_page_config(
        # 本地缓存目录
        WEB_RAM_PATH=f"{page_config.WORKSPAPCE}/WEB_ROM",
        # 图像绘制的配置目录
        CONFIG_PATH=f"{page_config.WEB_RAM_PATH}/configs",
        # 图像绘制的保存目录
        FIGURE_PATH=f"{page_config.WEB_RAM_PATH}/figures",
        # 端口
        PORT=args.port,
        # 账号
        USER_NAME=args.user_name,
        # 密码
        PASSWD=args.password
    )
    start_page_server()


if __name__ == "__main__":
    main()
