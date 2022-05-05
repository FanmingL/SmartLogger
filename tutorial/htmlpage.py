import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import smart_logger.common.page_config as page_config
import smart_logger.common.plot_config as plot_config
from smart_logger.front_page.page import start_page_server


def main():
    # 关键配置项1：数据目录，该目录下存有日志文件
    plot_config.DATA_PATH = '/full/path/to/data'
    # 关键配置项2：本地工作目录，该目录会自动创建，并会在里面写入一些缓存文件，如缓存的配置信息，绘制的曲线图
    page_config.WORKSPAPCE = os.path.expanduser('~/Desktop/small_logger_cache')

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
    # 图像绘制的保存目录
    page_config.FIGURE_PATH = f"{page_config.WEB_RAM_PATH}/figures"

    start_page_server()


if __name__ == "__main__":
    main()
