import os
import sys

from setuptools import setup, find_packages

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smart_logger'))
from version import __version__

setup(
    name="smart_logger",
    version=__version__,
    author="Fan-Ming Luo",
    author_email="luofm@lamda.nju.edu.cn",
    description="logger utility for reinforcement learning",

    # 项目主页
    url="https://github.com/FanmingL/SmartLogger",

    # 你要安装的包，通过 setuptools.find_packages 找到当前目录下有哪些包
    packages=find_packages(),
    install_requires=[
        'tensorboardX',
        'numpy',
        'paramiko',
        'matplotlib',
        'seaborn',
        'flask',
        'flask_cors',
        'simplejson',
        'Pillow',
        'pandas',
        'tensorboard',
    ]
)
