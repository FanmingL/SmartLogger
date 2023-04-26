import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import smart_logger.common.page_config as page_config
import smart_logger.common.plot_config as plot_config
from smart_logger.front_page.page import start_page_server
from sml_tutorial.generate_data import simulate_experiment


def main():
    logger_output_dir_list = simulate_experiment()
    # 数据目录
    plot_config.DATA_PATH = os.path.dirname(logger_output_dir_list[0])
    # 我们需要定义, 'policy_lr'且"information"都一致的是同一算法，这样就不用在页面里再次定义
    plot_config.DATA_MERGER = ['policy_lr', "information"]
    # 应该绘制哪些图像
    plot_config.PLOTTING_XY = [['timestep', 'performance'], ['timestep', 'evaluation']]
    # 在绘图的时候，从哪里加载数据绘制
    plot_config.PLOT_LOG_PATH = f"{plot_config.DATA_PATH}"
    # 绘图之后，将输出的图像文件存到哪里
    plot_config.PLOT_FIGURE_SAVING_PATH = f"{os.path.join(os.path.dirname(plot_config.DATA_PATH), 'figure')}"

    # 本地工作目录
    page_config.WORKSPAPCE = os.path.expanduser('~/Desktop')
    # 本地缓存目录
    page_config.WEB_RAM_PATH = f"{page_config.WORKSPAPCE}/WEB_ROM"
    # 图像绘制的配置目录
    page_config.CONFIG_PATH = f"{page_config.WEB_RAM_PATH}/configs"
    # 图像绘制的保存目录
    page_config.FIGURE_PATH = f"{page_config.WEB_RAM_PATH}/figures"

    start_page_server()


if __name__ == "__main__":
    main()
