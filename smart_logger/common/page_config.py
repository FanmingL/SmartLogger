# 网页登录的用户名
USER_NAME = "user"
# 网页登录密码
PASSWD = "123456"
# 网页名可以是一个IP，也可以是一个域名，通过访问"http://WEB_NAME:PORT"来访问实验整合页面
WEB_NAME = "127.0.0.1"
# 网页端口
PORT = 7005
# 本地工作目录
WORKSPAPCE = "/home/luofm/Data"
# 本地缓存目录
WEB_RAM_PATH = f"{WORKSPAPCE}/WEB_ROM"
# 图像绘制的配置目录
CONFIG_PATH = f"{WEB_RAM_PATH}/configs"
# 图像绘制的配置目录
USER_DATA_PATH = f"{WEB_RAM_PATH}/users"
# 图像绘制的保存目录
FIGURE_PATH = f"{WEB_RAM_PATH}/figures"
# 要将common_config的哪些配置也当成参数/配置
CONSIDERED_RUNNING_CONFIG = ['SHORT_NAME_SUFFIX', 'IMPORTANT_CONFIGS']
# PLOTTING的哪个配置是控制文件保存路径的
PLOTTING_SAVING_PATH_KEY = 'PLOT_FIGURE_SAVING_PATH'
# 将汇总文件缓存到哪里
TOTAL_FIGURE_FOLDER = f'full_path'
# COOKIE有效时长，即登录多久之后需要重新登录
COOKIE_PERIOD = 24
# 是否需要重复登录，False则不需要二次登录
REQUIRE_RELOGIN = True
