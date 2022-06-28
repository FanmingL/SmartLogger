from smart_logger.common.common_config import LOG_DIR_BACKING_NAME
# 绘图相关
DESCRIPTION = dict()
# 数据目录
DATA_PATH = "/home/luofm/Data"
# 在绘图的时候，从哪里加载数据绘制
PLOT_LOG_PATH = f"{DATA_PATH}/{LOG_DIR_BACKING_NAME}"
DESCRIPTION['PLOT_LOG_PATH'] = '绘图数据加载路径'
# 绘图之后，将输出的图像文件存到哪里
PLOT_FIGURE_SAVING_PATH = f"{DATA_PATH}/{LOG_DIR_BACKING_NAME}_figure"
# 绘图时，X-Y轴数据
PLOTTING_XY = [['timestep', 'EpRetTrain'], ['timestep', 'EpRetTest']]
# 曲线绘制顺序
PLOTTING_ORDER = []
# 曲线绘制顺序
LEGEND_ORDER = []
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
# 数据选择规则
DATA_SELECT = [
    {'information': "MAIN"},
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
DESCRIPTION['MAX_COLUMN'] = '子图最大列数'
# 是否平滑均值
USE_SMOOTH = True
DESCRIPTION['USE_SMOOTH'] = '是否平滑均值'
# 平滑半径
SMOOTH_RADIUS = 5
DESCRIPTION['SMOOTH_RADIUS'] = '平滑半径'
# 图例列数
LEGEND_COLUMN = 4
DESCRIPTION['LEGEND_COLUMN'] = '图例列数'
# 横坐标是否采用SCI格式
X_AXIS_SCI_FORM = True
DESCRIPTION['X_AXIS_SCI_FORM'] = '横坐标是否采用SCI格式'

# 需要上传生成的哪些图片到远程
FIGURE_TO_SYNC = ['total_curve.png', 'total_curve.pdf']

# 远程服务器的IP地址
FIGURE_SERVER_MACHINE_IP = "127.0.0.1"
DESCRIPTION['FIGURE_SERVER_MACHINE_IP'] = '远程服务器的IP地址'
# 远程服务器的端口
FIGURE_SERVER_MACHINE_PORT = 22
DESCRIPTION['FIGURE_SERVER_MACHINE_PORT'] = '远程服务器的端口'
# 远程服务器的登录账号
FIGURE_SERVER_MACHINE_USER = "root"
DESCRIPTION['FIGURE_SERVER_MACHINE_USER'] = '远程服务器的登录账号'
# 远程服务器的登录密码
FIGURE_SERVER_MACHINE_PASSWD = None
DESCRIPTION['FIGURE_SERVER_MACHINE_PASSWD'] = '远程服务器的登录密码'
# 将日志文件发到远程服务器的哪一个路径下
FIGURE_SERVER_MACHINE_TARGET_PATH = f"/var/data/"
DESCRIPTION['FIGURE_SERVER_MACHINE_TARGET_PATH'] = '将日志文件发到远程服务器的哪一个路径下'
# 在标题里加入当前日期，方便知道什么时候更新的这张图
RECORD_DATE_TIME = True
DESCRIPTION['RECORD_DATE_TIME'] = '是否在标题里加入图片绘制日期'
# 子图之间的横向间隔
SUBPLOT_WSPACE = 0.2
DESCRIPTION['SUBPLOT_WSPACE'] = '子图之间的横向间隔'
# 子图之间的纵向间隔
SUBPLOT_HSPACE = 0.1
DESCRIPTION['SUBPLOT_HSPACE'] = '子图之间的纵向间隔'
# 图例的位置X
LEGEND_POSITION_X = 0.
DESCRIPTION['LEGEND_POSITION_X'] = '图例的横向位置'
# 图例的位置Y
LEGEND_POSITION_Y = -0.33
DESCRIPTION['LEGEND_POSITION_Y'] = '图例纵向位置'
# 最大并行进程数量
PROCESS_NUM = 5
DESCRIPTION['PROCESS_NUM'] = '绘图最大允许进程数'
# 最大并行进程数量
PROCESS_NUM_LOAD_DATA = 5
DESCRIPTION['PROCESS_NUM_LOAD_DATA'] = '数据加载进程数'
# 最大并行进程数量
THREAD_NUM = 5
DESCRIPTION['THREAD_NUM'] = '每个进程的线程数'
# 子图宽度
SUBFIGURE_WIDTH = 6.4
DESCRIPTION['SUBFIGURE_WIDTH'] = '子图宽度'
# 子图高度
SUBFIGURE_HEIGHT = 4.48
DESCRIPTION['SUBFIGURE_HEIGHT'] = '子图高度'
# 存图DPI
PNG_DPI = 150
DESCRIPTION['PNG_DPI'] = 'PNG图像DPI'
# 标签字体大小
FONTSIZE_LABEL = 18
DESCRIPTION['FONTSIZE_LABEL'] = '横纵轴标签字体大小'
# 图例字体大小
FONTSIZE_LEGEND = 15
DESCRIPTION['FONTSIZE_LEGEND'] = '图例字体大小'
# 标题字体大小
FONTSIZE_TITLE = 18
DESCRIPTION['FONTSIZE_TITLE'] = '标题字体大小'
# 横坐标刻度的字体大小
FONTSIZE_XTICK = 18
DESCRIPTION['FONTSIZE_XTICK'] = '横轴刻度字体大小'
# 纵坐标刻度的字体大小
FONTSIZE_YTICK = 18
DESCRIPTION['FONTSIZE_YTICK'] = '纵轴刻度字体大小'

# 大标题字体大小
FONTSIZE_SUPTITLE = 15
DESCRIPTION['FONTSIZE_SUPTITLE'] = '大标题字体大小'

# 大标题位置
SUPTITLE_Y = 0.99
DESCRIPTION['SUPTITLE_Y'] = '大标题纵向位置'
# X轴的最大值
XMAX = 'None'
DESCRIPTION['XMAX'] = 'X轴的最大值'
# 重点算法
PRIMARY_ALG = 'None'
DESCRIPTION['PRIMARY_ALG'] = '重点算法, 即图例排第一的算法名'
# 线宽
LINE_WIDTH = 2.0
DESCRIPTION['LINE_WIDTH'] = '线宽'
# Marker大小
MARKER_SIZE = 8.0
DESCRIPTION['MARKER_SIZE'] = '线标记大小'
# 是否在图例中体现种子个数
SHOW_SEED_NUM = False
DESCRIPTION['SHOW_SEED_NUM'] = '是否在图例中体现种子个数'
# 导出的图像的名字
FINAL_OUTPUT_NAME = "total_curve"
DESCRIPTION['FINAL_OUTPUT_NAME'] = '导出的图像的名字'
# 储存的图像文件的前缀
OUTPUT_FILE_PREFIX = "None"
DESCRIPTION['OUTPUT_FILE_PREFIX'] = "储存的图像文件的前缀"
# 是否需要SUP_TITLE
NEED_SUP_TITLE = True
DESCRIPTION['NEED_SUP_TITLE'] = '是否需要大标题'

# 将Y轴的label固定
FIXED_Y_LABEL = None
DESCRIPTION['FIXED_Y_LABEL'] = '自定义Y轴label名'

# 标题命名方法
TITLE_NAME_IDX = None
DESCRIPTION['TITLE_NAME_IDX'] = '标题根据什么进行定义'

# 阴影透明度
SHADING_ALPHA = 0.2
DESCRIPTION['SHADING_ALPHA'] = '阴影透明度'

# 是否使用图例边框
USE_LEGEND_FRAME = True
DESCRIPTION['USE_LEGEND_FRAME'] = '是否使用图例边框'

TITLE_SUFFIX = "None"
DESCRIPTION['TITLE_SUFFIX'] = '标题尾缀'

PLOT_FOR_EVERY = 1
DESCRIPTION['PLOT_FOR_EVERY'] = '绘图数据的下采样间隔'

USE_IGNORE_RULE = True
DESCRIPTION['USE_IGNORE_RULE'] = '是否使用过滤规则'

TABLE_BOLD_MAX = True
DESCRIPTION['TABLE_BOLD_MAX'] = '表格是否加粗最高值'
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