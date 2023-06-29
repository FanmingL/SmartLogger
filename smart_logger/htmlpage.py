import argparse
import os

import smart_logger.common.page_config as page_config
import smart_logger.common.plot_config as plot_config
from smart_logger.front_page.page import start_page_server


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
    parser.add_argument('--title', '-t', type=str, default='None',
                        help="page title prefix")
    parser.add_argument('--port', '-p', type=int, default=7005,
                        help="Server port")
    parser.add_argument('--login_free', '-lf', action='store_true',
                        help='Do not require login.')
    parser.add_argument('--log_to_file', '-ltf', action='store_true',
                        help='whether to log to file.', default=False)
    args = parser.parse_args()
    # 关键配置项1：数据目录，该目录下存有日志文件
    plot_config.DATA_PATH = os.path.abspath(args.data_path)
    # 关键配置项2：本地工作目录，该目录会自动创建，并会在里面写入一些缓存文件，如缓存的配置信息，绘制的曲线图
    page_config.WORKSPAPCE = os.path.abspath(os.path.expanduser(args.workspace_path))

    # 如何判断哪些日志会被看作是同一个算法
    plot_config.DATA_MERGER = []
    # 应该绘制哪些图像
    plot_config.PLOTTING_XY = []
    # 在绘图的时候，从哪里加载数据绘制
    plot_config.PLOT_LOG_PATH = f"{plot_config.DATA_PATH}"
    # 绘图之后，将输出的图像文件存到哪里
    plot_config.PLOT_FIGURE_SAVING_PATH = f"{os.path.join(os.path.dirname(plot_config.DATA_PATH), 'figure')}"

    # 本地缓存目录
    page_config.WEB_RAM_PATH = f"{page_config.WORKSPAPCE}/WEB_ROM"
    # 图像绘制的配置目录
    page_config.CONFIG_PATH = f"{page_config.WEB_RAM_PATH}/configs"
    # 图像绘制的配置目录
    page_config.USER_DATA_PATH = f"{page_config.WEB_RAM_PATH}/users"
    # 图像绘制的保存目录
    page_config.FIGURE_PATH = f"{page_config.WEB_RAM_PATH}/figures"
    # 端口
    page_config.PORT = args.port
    # 账号
    page_config.USER_NAME = args.user_name
    # 密码
    page_config.PASSWD = args.password
    page_config.REQUIRE_RELOGIN = not args.login_free
    # 标题
    page_config.PAGE_TITLE_PREFIX = args.title if not str(args.title) == 'None' else None
    # 是否保存日志入文件
    page_config.PAGE_LOG_TO_FILE = args.log_to_file
    start_page_server()


if __name__ == "__main__":
    main()
