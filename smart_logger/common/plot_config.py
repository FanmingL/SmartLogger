from smart_logger.common.common_config import LOG_DIR_BACKING_NAME

# 绘图相关
DESCRIPTION = dict()
FLEXIBLE_CONFIG = dict()
FIXED_PARAMETER = {'FLEXIBLE_CONFIG', 'FIXED_PARAMETER', 'DESCRIPTION'}
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
DATA_IGNORE_PROPERTY = [
    {'information': {}},
    {'information': {}},
    {'SHORT_NAME_SUFFIX': {}},
]
# 数据选择规则
DATA_SELECT = [
    {'information': "MAIN"},
]
DATA_SELECT_PROPERTY = [
    {'information': {}}
]
# 回收站
DATA_IGNORE_GARBAGE = [

]

DATA_SELECT_GARBAGE = [

]
DATA_IGNORE_PROPERTY_GARBAGE = [

]

DATA_SELECT_PROPERTY_GARBAGE = [

]
# 图例重命名规则
SHORT_NAME_FROM_CONFIG = {
}
SHORT_NAME_FROM_CONFIG_PROPERTY = {
}
# 数据键重命名规则
DATA_KEY_RENAME_CONFIG = {
    'TotalInteraction': 'timestep',
    'EpRet': 'EpRetTrain',
}

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

PLOT_MODE = 'CURVE'
DESCRIPTION['PLOT_MODE'] = '绘图模型 (CURVE, BAR)'

# 一行子图最多多少列
MAX_COLUMN = 3
DESCRIPTION['MAX_COLUMN'] = '子图最大列数 (1, 2, ...)'

# 图例列数
LEGEND_COLUMN = 4
DESCRIPTION['LEGEND_COLUMN'] = '图例列数 (1, 2, ...)'
FLEXIBLE_CONFIG['LEGEND_COLUMN'] = dict(SAME_XY=True)

# 是否平滑均值
USE_SMOOTH = True
DESCRIPTION['USE_SMOOTH'] = '是否平滑均值 (True, False)'
FLEXIBLE_CONFIG['USE_SMOOTH'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 平滑半径
SMOOTH_RADIUS = 5
DESCRIPTION['SMOOTH_RADIUS'] = '平滑半径 (1, 2, ...)'
FLEXIBLE_CONFIG['SMOOTH_RADIUS'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

PLOT_FOR_EVERY = 1
DESCRIPTION['PLOT_FOR_EVERY'] = '绘图数据的下采样间隔 (1, 2, ...)'
FLEXIBLE_CONFIG['PLOT_FOR_EVERY'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# X轴的最大值
XMAX = 'None'
DESCRIPTION['XMAX'] = 'X轴的最大值 (None, 1, 2, ...)'
FLEXIBLE_CONFIG['XMAX'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# Y轴最小值的最大值
YMIN = 'None'
DESCRIPTION['YMIN'] = 'Y轴的最小值 (None, 1, 2, ...)'
FLEXIBLE_CONFIG['YMIN'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 最少允许的有效数据点个数
MINIMUM_DATA_POINT_NUM = 'None'
DESCRIPTION['MINIMUM_DATA_POINT_NUM'] = '最少允许的有效数据点个数 (None, 0, 1, ...)'

# 最大并行进程数量
PROCESS_NUM = 5
DESCRIPTION['PROCESS_NUM'] = '绘图最大允许进程数 (1, 2, ...)'

# 最大数据读取并行进程数量
PROCESS_NUM_LOAD_DATA = 5
DESCRIPTION['PROCESS_NUM_LOAD_DATA'] = '数据加载进程数 (1, 2, ...)'

# 最大并行线程数量
THREAD_NUM = 5
DESCRIPTION['THREAD_NUM'] = '每个进程的线程数 (1, 2, ...)'

# 子图宽度
SUBFIGURE_WIDTH = 6.4
DESCRIPTION['SUBFIGURE_WIDTH'] = '子图宽度 (1.0, 2.0, ...)'
# 子图高度
SUBFIGURE_HEIGHT = 4.48
DESCRIPTION['SUBFIGURE_HEIGHT'] = '子图高度 (1.0, 2.0, ...)'

# 子图之间的横向间隔
SUBPLOT_WSPACE = 0.2
DESCRIPTION['SUBPLOT_WSPACE'] = '子图之间的横向间隔 (0.1, 0.2, ...)'
FLEXIBLE_CONFIG['SUBPLOT_WSPACE'] = dict(SAME_XY=True)

# 子图之间的纵向间隔
SUBPLOT_HSPACE = 0.4
DESCRIPTION['SUBPLOT_HSPACE'] = '子图之间的纵向间隔 (0.1, 0.2, ...)'
FLEXIBLE_CONFIG['SUBPLOT_HSPACE'] = dict(SAME_XY=True)

# 图例的位置X
LEGEND_POSITION_X = 0.0
DESCRIPTION['LEGEND_POSITION_X'] = '图例的横向位置 (-0.1, 0.0, 0.2, ...)'
FLEXIBLE_CONFIG['LEGEND_POSITION_X'] = dict(SAME_XY=True)

# 图例的位置Y
LEGEND_POSITION_Y = -0.18
DESCRIPTION['LEGEND_POSITION_Y'] = '图例纵向位置 (-0.1, 0.0, 0.2, ...)'
FLEXIBLE_CONFIG['LEGEND_POSITION_Y'] = dict(SAME_XY=True)

# 图例锚点位置
LEGEND_WHICH_POSITION = 'upper left'
DESCRIPTION['LEGEND_WHICH_POSITION'] = '图例锚点位置 (upper left, lower right, ...)'
FLEXIBLE_CONFIG['LEGEND_WHICH_POSITION'] = dict(SAME_XY=True)

# 大标题位置
SUPTITLE_Y = 0.99
DESCRIPTION['SUPTITLE_Y'] = '大标题纵向位置 (0.99, 0.999, ...)'
FLEXIBLE_CONFIG['SUPTITLE_Y'] = dict(SAME_XY=True)

# 标签字体大小
FONTSIZE_LABEL = 22
DESCRIPTION['FONTSIZE_LABEL'] = '横纵轴标签字体大小 (1, 2, ...)'
FLEXIBLE_CONFIG['FONTSIZE_LABEL'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 图例字体大小
FONTSIZE_LEGEND = 22
DESCRIPTION['FONTSIZE_LEGEND'] = '图例字体大小 (1, 2, ...)'
FLEXIBLE_CONFIG['FONTSIZE_LEGEND'] = dict(SAME_XY=True)

# 标题字体大小
FONTSIZE_TITLE = 22
DESCRIPTION['FONTSIZE_TITLE'] = '标题字体大小 (1, 2, ...)'
FLEXIBLE_CONFIG['FONTSIZE_TITLE'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 横坐标刻度的字体大小
FONTSIZE_XTICK = 22
DESCRIPTION['FONTSIZE_XTICK'] = '横轴刻度字体大小 (1, 2, ...)'
FLEXIBLE_CONFIG['FONTSIZE_XTICK'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 纵坐标刻度的字体大小
FONTSIZE_YTICK = 22
DESCRIPTION['FONTSIZE_YTICK'] = '纵轴刻度字体大小 (1, 2, ...)'
FLEXIBLE_CONFIG['FONTSIZE_YTICK'] = dict(SAME_XY=True)

# 大标题字体大小
FONTSIZE_SUPTITLE = 22
DESCRIPTION['FONTSIZE_SUPTITLE'] = '大标题字体大小 (1, 2, ...)'
FLEXIBLE_CONFIG['FONTSIZE_SUPTITLE'] = dict(SAME_XY=True)


# 线宽
LINE_WIDTH = 2.0
DESCRIPTION['LINE_WIDTH'] = '线宽 (1.0, 1.5, ...)'
FLEXIBLE_CONFIG['LINE_WIDTH'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# Marker大小
MARKER_SIZE = 8.0
DESCRIPTION['MARKER_SIZE'] = '线标记大小 (1.0, 1.5, ...)'
FLEXIBLE_CONFIG['MARKER_SIZE'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 阴影透明度
SHADING_ALPHA = 0.2
DESCRIPTION['SHADING_ALPHA'] = '阴影透明度 (1.0, 1.5, ...)'
FLEXIBLE_CONFIG['SHADING_ALPHA'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 导出的图像的名字
FINAL_OUTPUT_NAME = "total_curve"
DESCRIPTION['FINAL_OUTPUT_NAME'] = '导出的图像的名字'

# 存图DPI
PNG_DPI = 150
DESCRIPTION['PNG_DPI'] = 'PNG图像DPI (100, 101, ...)'
FLEXIBLE_CONFIG['PNG_DPI'] = dict(SAME_XY=True)

# 表格有效位数
TABLE_VALID_BITS = 2
DESCRIPTION['TABLE_VALID_BITS'] = '表格中有效位数 (0, 1, ...)'
FLEXIBLE_CONFIG['TABLE_VALID_BITS'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 算法最低相对性能
MIN_RELATIVE_PERFORMANCE = 0.0
DESCRIPTION['MIN_RELATIVE_PERFORMANCE'] = '算法最低相对性能 (0.0, 0.1, ...)'
FLEXIBLE_CONFIG['MIN_RELATIVE_PERFORMANCE'] = dict(SAME_XY=True)

# 储存的图像文件的前缀
OUTPUT_FILE_PREFIX = "None"
DESCRIPTION['OUTPUT_FILE_PREFIX'] = "储存的图像文件的前缀 (None, xxx, ...)"
FLEXIBLE_CONFIG['OUTPUT_FILE_PREFIX'] = dict(SAME_XY=True)

# 是否需要重采样
REQUIRE_RESAMPLE = None
DESCRIPTION['REQUIRE_RESAMPLE'] = '是否需要重采样 (None, True, False)'
FLEXIBLE_CONFIG['REQUIRE_RESAMPLE'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 将Y轴的label固定
FIXED_Y_LABEL = None
DESCRIPTION['FIXED_Y_LABEL'] = '自定义Y轴label名 (None, xxx, ...)'
FLEXIBLE_CONFIG['FIXED_Y_LABEL'] = dict(SAME_XY=True)

# 标题命名方法
TITLE_NAME_IDX = None
DESCRIPTION['TITLE_NAME_IDX'] = '标题根据什么进行定义 (None, -1, 0, ...)'

# 标题命名方法
BAR_TICK_NAME_IDX = None
DESCRIPTION['BAR_TICK_NAME_IDX'] = '直方图刻度根据什么进行定义 (None, -1, 0, ...)'

BAR_INTERVAL = 0.18
DESCRIPTION['BAR_INTERVAL'] = '直方图不同区域的间隔 (0.0, 0.1, 0.2, ...)'
FLEXIBLE_CONFIG['BAR_INTERVAL'] = dict(SAME_XY=True)

BAR_NORMALIZE_VALUE = True
DESCRIPTION['BAR_NORMALIZE_VALUE'] = '直方图值归一化 (True, False)'
FLEXIBLE_CONFIG['BAR_NORMALIZE_VALUE'] = dict(SAME_XY=True)

BAR_MARK_MAXIMUM = False
DESCRIPTION['BAR_MARK_MAXIMUM'] = '标星最大值 (True, False)'
FLEXIBLE_CONFIG['BAR_MARK_MAXIMUM'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

BAR_MAXIMUM_EXCLUDE = None
DESCRIPTION['BAR_MAXIMUM_EXCLUDE'] = '统计最大值时排除某算法，逗号分隔 (None, baseline, ...)'
FLEXIBLE_CONFIG['BAR_MAXIMUM_EXCLUDE'] = dict(SAME_XY=True)

BAR_HOLLOW_ALG_NAME = None
DESCRIPTION['BAR_HOLLOW_ALG_NAME'] = '虚化绘制的算法，至多一个 (None, baseline, ...)'

BAR_NORMALIZE_MINIMUM_VALUE = -1.0
DESCRIPTION['BAR_NORMALIZE_MINIMUM_VALUE'] = '直方图值归一化最小值 (-0.0, -0.5, -1.0, ...)'
FLEXIBLE_CONFIG['BAR_NORMALIZE_MINIMUM_VALUE'] = dict(SAME_XY=True)

BAR_SORT_X = False
DESCRIPTION['BAR_SORT_X'] = '直方图排序 (True, False)'
FLEXIBLE_CONFIG['BAR_SORT_X'] = dict(SAME_XY=True)

TITLE_SUFFIX = "None"
DESCRIPTION['TITLE_SUFFIX'] = '标题尾缀 (None, xxx, ...)'
FLEXIBLE_CONFIG['TITLE_SUFFIX'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 是否需要SUP_TITLE
NEED_SUP_TITLE = True
DESCRIPTION['NEED_SUP_TITLE'] = '是否需要大标题 (True, False)'
FLEXIBLE_CONFIG['NEED_SUP_TITLE'] = dict(SAME_XY=True)

# 在大标题里加入当前日期，方便知道什么时候更新的这张图
RECORD_DATE_TIME = True
DESCRIPTION['RECORD_DATE_TIME'] = '是否在大标题里加入图片绘制日期 (True, False)'
FLEXIBLE_CONFIG['RECORD_DATE_TIME'] = dict(SAME_XY=True)

#
REPORT_PCA_EVAL = False
DESCRIPTION['REPORT_PCA_EVAL'] = '在标题中体现算法差异程度指标 (True, False)'
FLEXIBLE_CONFIG['REPORT_PCA_EVAL'] = dict(SAME_XY=True)

# 纵坐标科学计数法
Y_AXIS_SCI_FORM = False
DESCRIPTION['Y_AXIS_SCI_FORM'] = '纵坐标科学计数法 (True, False)'
FLEXIBLE_CONFIG['Y_AXIS_SCI_FORM'] = dict(SAME_XY=True)

# 横坐标是否采用SCI格式
X_AXIS_SCI_FORM = True
DESCRIPTION['X_AXIS_SCI_FORM'] = '横坐标科学计数法 (True, False)'
FLEXIBLE_CONFIG['X_AXIS_SCI_FORM'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 是否在图例中体现种子个数
SHOW_SEED_NUM = False
DESCRIPTION['SHOW_SEED_NUM'] = '是否在图例中体现种子个数 (True, False)'
FLEXIBLE_CONFIG['SHOW_SEED_NUM'] = dict(SAME_XY=True)

# 是否在条形图中体现种子个数
SHOW_BAR_SEED_NUM = True
DESCRIPTION['SHOW_BAR_SEED_NUM'] = '是否在条形图中体现种子个数 (True, False)'
FLEXIBLE_CONFIG['SHOW_BAR_SEED_NUM'] = dict(SAME_XY=True, SAME_TITLE=True, SUB_IMAGE=True)

# 是否使用图例边框
USE_LEGEND_FRAME = True
DESCRIPTION['USE_LEGEND_FRAME'] = '是否使用图例边框 (True, False)'
FLEXIBLE_CONFIG['USE_LEGEND_FRAME'] = dict(SAME_XY=True)

# 是否按照平均性能为图例排序
SORT_BY_PERFORMANCE_ORDER = False
DESCRIPTION['SORT_BY_PERFORMANCE_ORDER'] = '是否按照平均性能为图例排序 (True, False)'
FLEXIBLE_CONFIG['SORT_BY_PERFORMANCE_ORDER'] = dict(SAME_XY=True)

USE_IGNORE_RULE = True
DESCRIPTION['USE_IGNORE_RULE'] = '是否使用过滤规则'

TABLE_BOLD_MAX = True
DESCRIPTION['TABLE_BOLD_MAX'] = '表格是否加粗最高值'

AUTO_PLOTTING = False
DESCRIPTION['AUTO_PLOTTING'] = '是否自动刷新绘图'

AUTO_PLOTTING_INTERVAL = 600
DESCRIPTION['AUTO_PLOTTING_INTERVAL'] = '自动绘图时间间隔(秒) (300, 600, ...)'

AUTO_PLOTTING_TURN_ON_TIME = '2023-05-01 00:00:00'
DESCRIPTION['AUTO_PLOTTING_TURN_ON_TIME'] = '使能自动绘图的日期'

MAX_AUTO_PLOTTING_NUM = 3
DESCRIPTION['MAX_AUTO_PLOTTING_NUM'] = '最大同时自动绘图数量'

FOCUS_IMAGE_CONFIG_GROUP = 'default'
DESCRIPTION['FOCUS_IMAGE_CONFIG_GROUP'] = '图像绘制配置的图组选择'

FOCUS_IMAGE_CONFIG_SAME_CONTENT_GROUP = 'None'
DESCRIPTION['FOCUS_IMAGE_CONFIG_SAME_CONTENT_GROUP'] = '图像绘制配置的同内容图组选择'

FOCUS_IMAGE_CONFIG_SUB_IMAGE_TITLE = 'None'
DESCRIPTION['FOCUS_IMAGE_CONFIG_SUB_IMAGE_TITLE'] = '图像绘制配置的子图选择'

PARAMETER_ADJUST_USE_CACHE = False
DESCRIPTION['PARAMETER_ADJUST_USE_CACHE'] = '绘图参数界面使用缓存'

ADDITIONAL_PLOT_CONFIGS = dict()
DESCRIPTION['ADDITIONAL_PLOT_CONFIGS'] = '针对性绘图配置'

TABLE_ALG_SORT_BY_ROW = False
DESCRIPTION['TABLE_ALG_SORT_BY_ROW'] = '表格算法按行排列'
FLEXIBLE_CONFIG['TABLE_ALG_SORT_BY_ROW'] = dict(SAME_XY=True)

# ADDITIONAL_PLOT_CONFIGS['pair_image']
# ADDITIONAL_PLOT_CONFIGS['same_title']
# ADDITIONAL_PLOT_CONFIGS['sole_image']

# ADDITIONAL_PLOT_CONFIGS['pair_image'][XY]
# ADDITIONAL_PLOT_CONFIGS['same_title'][title]
# ADDITIONAL_PLOT_CONFIGS['sole_image'][XY][title]


# 配置结束

def get_global_plot_configs(things):
    res = dict()
    for k, v in things:
        if not k.startswith('__') and not hasattr(v, '__call__') and 'module' not in str(type(v)) and k not in FIXED_PARAMETER:
            res[k] = v
    return res


def global_plot_configs(things=[*locals().items()]):
    return get_global_plot_configs(things)
