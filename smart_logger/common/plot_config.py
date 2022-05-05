from smart_logger.common.common_config import LOG_DIR_BACKING_NAME
# 绘图相关
# 数据目录
DATA_PATH = "/home/luofm/Data"
# 在绘图的时候，从哪里加载数据绘制
PLOT_LOG_PATH = f"{DATA_PATH}/{LOG_DIR_BACKING_NAME}"
# 绘图之后，将输出的图像文件存到哪里
PLOT_FIGURE_SAVING_PATH = f"{DATA_PATH}/{LOG_DIR_BACKING_NAME}_figure"
# 绘图时，X-Y轴数据
PLOTTING_XY = [['timestep', 'EpRetTrain'], ['timestep', 'EpRetTest']]
# 不同图片之间的数据，按照FIGURE_SEPARATION分开
FIGURE_SEPARATION = ['env_name']
# DATA_MERGER中所包含的量的值都一样的，看成是同一种数据
DATA_MERGER = ['SHORT_NAME_SUFFIX', "information", "learn_embedding"]
# 数据过滤规则
DATA_IGNORE = [
    {'information': "test_speed"},
    {'information': "local_test"},
    {'SHORT_NAME_SUFFIX': "test_speed"},
]
# 图例重命名规则
SHORT_NAME_FROM_CONFIG = {
}
# 数据键重命名规则
DATA_KEY_RENAME_CONFIG = {
    'TotalInteraction': 'timestep',
    'EpRet': 'EpRetTrain',
}
# 一行子图最多多少列
MAX_COLUMN = 3
# 是否平滑均值
USE_SMOOTH = True
# 平滑半径
SMOOTH_RADIUS = 5
# 图例列数
LEGEND_COLUMN = 4
# 横坐标是否采用SCI格式
X_AXIS_SCI_FORM = True

# 需要上传生成的哪些图片到远程
FIGURE_TO_SYNC = ['total_curve.png', 'total_curve.pdf']

# 远程服务器的IP地址
FIGURE_SERVER_MACHINE_IP = "127.0.0.1"
# 远程服务器的端口list
FIGURE_SERVER_MACHINE_PORT = 22
# 远程服务器的登录账号
FIGURE_SERVER_MACHINE_USER = "root"
# 远程服务器的登录密码
FIGURE_SERVER_MACHINE_PASSWD = None
# 将日志文件发到远程服务器的哪一个路径下
FIGURE_SERVER_MACHINE_TARGET_PATH = f"/var/data/"
# 在标题里加入当前日期，方便知道什么时候更新的这张图
RECORD_DATE_TIME = True
# 子图之间的横向间隔
SUBPLOT_WSPACE = 0.2
# 子图之间的纵向间隔
SUBPLOT_HSPACE = 0.1
# 图例的位置X
LEGEND_POSITION_X = 0.
# 图例的位置Y
LEGEND_POSITION_Y = -0.33
# 最大并行进程数量
PROCESS_NUM = 5
# 子图宽度
SUBFIGURE_WIDTH = 6.4
# 子图高度
SUBFIGURE_HEIGHT = 4.48
# 存图DPI
PNG_DPI = 300
# 标签字体大小
FONTSIZE_LABEL = 18
# 图例字体大小
FONTSIZE_LEGEND = 15
# 标题字体大小
FONTSIZE_TITLE = 18
# 横坐标刻度的字体大小
FONTSIZE_XTICK = 10
# 纵坐标刻度的字体大小
FONTSIZE_YTICK = 10

# 大标题字体大小
FONTSIZE_SUPTITLE = 15
# 大标题位置
SUPTITLE_Y = 0.98
# 配置结束
def get_global_plot_configs(things):
    res = dict()
    for k, v in things:
        if not k.startswith('__') and not hasattr(v, '__call__') and 'module' not in str(type(v)):
            res[k] = v
    return res


def global_plot_configs(things=[*locals().items()]):
    return get_global_plot_configs(things)


if __name__ == '__main__':
    for k, v in global_plot_configs().items():
        print(f'{k}: {v}')