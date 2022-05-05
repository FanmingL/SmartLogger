import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smart_logger.report.plotting import plot
import smart_logger.common.plot_config as plot_config
from tutorial.generate_data import simulate_experiment


def main():
    logger_output_dir_list = simulate_experiment()
    # 我们需要定义, 'policy_lr'且"information"都一致的是同一算法
    plot_config.DATA_MERGER = ['policy_lr', "information"]
    # 每个子图之中，绘制'env_name'一样的数据
    plot_config.FIGURE_SEPARATION = ['env_name']
    # 数据目录
    plot_config.DATA_PATH = os.path.dirname(logger_output_dir_list[0])
    # 在绘图的时候，从哪里加载数据绘制
    plot_config.PLOT_LOG_PATH = f"{plot_config.DATA_PATH}"
    # 绘图之后，将输出的图像文件存到哪里
    plot_config.PLOT_FIGURE_SAVING_PATH = f"{os.path.join(plot_config.DATA_PATH, 'figure')}"
    print(f'we will load data in {plot_config.PLOT_LOG_PATH} to plot')
    print(f'we will save figure to {plot_config.PLOT_FIGURE_SAVING_PATH} to plot')
    # 应该绘制哪些图像
    plot_config.PLOTTING_XY = [['timestep', 'performance'], ['timestep', 'evaluation']]
    # 对图例进行重命名，可以把以下这个赋值去掉重新绘图，即可理解这句话的意思，若不进行命名，代码会基于plot_config.DATA_MERGER进行自动命名
    plot_config.SHORT_NAME_FROM_CONFIG = {
        'test_for_plot+0.1': 'lr_0.1',
        'test_for_plot+0.01': 'lr_0.01',
        'test_for_plot+0.001': 'lr_0.001',
    }
    # 直接绘图
    plot()


if __name__ == '__main__':
    main()

