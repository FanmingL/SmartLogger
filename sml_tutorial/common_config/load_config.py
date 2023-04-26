import os

import smart_logger


def init_smart_logger():
    base_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
    smart_logger.init_config('common_config/common_config.yaml',
                             'common_config/experiment_config.yaml',
                             base_path
                             )
