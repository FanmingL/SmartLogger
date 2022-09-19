# 标准初始化方法
from parameter.Parameter import Parameter
from smart_logger import Logger
import os
from common_config.load_config import init_smart_logger
import random
from smart_logger import logger_from_param


class Demo:
    def __init__(self):
        # 实例化参数, 此处解析输入为参数
        self.parameter = Parameter()
        # 实例化logger，这里，我们根据参数来调整logger的文件的保存位置
        self.logger = Logger(log_name=self.parameter.short_name, log_signature=self.parameter.signature)
        # 设置parameter的logger
        self.parameter.set_logger(self.logger)
        # 设置parameter的保存路径
        self.parameter.set_config_path(os.path.join(self.logger.output_dir, 'config'))
        # 保存parameter
        self.parameter.save_config()
        # 以上的命令可以通过直接执行以下命令得到，可以少记很多代码
        # self.logger, self.parameter = logger_from_param(Parameter())

    def run(self):
        for _ in range(10):
            # 随机报错
            if random.random() < 0.05:
                raise Exception("Randomized exception!!")
            self.logger.log_tabular('a', 2)
            self.logger.log_tabular('b', 1)
            self.logger.dump_tabular()

            self.logger.sync_log_to_remote()


def main():
    init_smart_logger()
    demo = Demo()
    demo.run()


if __name__ == '__main__':
    main()

