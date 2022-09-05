[TOC]

# 集成教程

本教程介绍如何将本套工具集应用至训练中。目的是在代码中只要

1. 加入一个带有三个文件的文件夹

2. 定义参数文件

3. 加入几行实例化参数、logger的代码

4. 加入一行备份日志的代码

就能够将每个日志单独、隔离的并行运行，同时可定期主动将日志备份至远程服务器。

# 详细步骤
根据以下步骤我们可以将`sml_tutorial`中的`common_config`, `parameter`, `main_logger_and_parameter.py`构造出来，具体可以直接以[main_logger_and_parameter.py](sml_tutorial/main_logger_and_parameter.py)作为入口查看。
## 1. 复制common_config目录

**将[common_config](sml_tutorial/common_config)这个文件夹复制到你的工程的根目录**。

其中包括三个文件`common_config.yaml`, `experiment_config.yaml`, `load_config.py`，这三个文件的作用分别为

- `common_config.yaml`，通用配置，用于配置(1)启动时，将哪些文件夹备份，哪些文件夹不备份；(2)将日志备份至远程时，远程机器IP、密码、端口、用户、路径等；(3)日志存储的路径的文件夹名。
- `experiment_config.yaml`，(1)程序运行时的一些独有配置，可以在此定义一些变量，在程序中通过smart_logger的接口即可读取到在此定义的变量的值；(2)配置储存当前日志文件的文件夹的名字
- `load_config.py`，关键在于定义`base_path`，默认一次运行的所有日志文件都会存到`base_path/logfile`中的某个子文件夹中，建议`base_path`索引的位置就是程序的根目录。

`common_config.yaml`

```yaml
# 文件备份相关
# 在备份运行代码至日志文件时，文件夹按照以下开头的，将不会被备份过去
BACKUP_IGNORE_HEAD:
- __p
- .
# 在备份运行代码至日志文件时，文件夹含有以下的关键字的，将不会被备份过去
BACKUP_IGNORE_KEY:
- logfile
- logfile_bk
- baselines
# 在备份运行代码至日志文件时，文件夹按照以下结尾的，将不会被备份过去
BACKUP_IGNORE_TAIL: []
# 日志系统根目录，设null即可，后续会有py代码覆盖
BASE_PATH: null
# 将日志同步到远程时，目标文件夹名
LOG_DIR_BACKING_NAME: TESTLog
# 日志路径名
LOG_FOLDER_NAME: logfile
# 备份日志路径名，写日志时若logfile中已经存在某个日志，将会先把日志移到logfile_bk，再往logfile中写新的日志
LOG_FOLDER_NAME_BK: logfile_bk
# 远程机器IP，远程备份时，会像该IP，发送日志数据，可以设定多个IP，若前面的IP传送失败时，会自动使用下一个IP
MAIN_MACHINE_IP:
- 127.0.0.1
# 远程数据存储路径，TESTLog需要与LOG_DIR_BACKING_NAME一致
MAIN_MACHINE_LOG_PATH: /home/luofm/Data/TESTLog
# 远程机器密码
MAIN_MACHINE_PASSWD: xxxxxxx
# 远程机器IP对应的端口（ssh端口）
MAIN_MACHINE_PORT:
- 22
# 远程机器登录用户名
MAIN_MACHINE_USER: user_name
# 不用管
WORKSPACE_PATH: /home/luofm/Data
```

`experiment_config.yaml`

```yaml
# 实验相关的一些变量值设定，可以通过smart_logger.get_customized_value("demo_variable")得到其值
EXPERIMENT_COMMON_PARAMETERS:
  demo_variable: test
# 实验目标，会存到日志的实验配置文件中，也会在实验开始的时候打印一下
EXPERIMENT_TARGET: "RELEASE"
# 用以下参数对日志文件夹命名，现在这样命名的可能是Hopper-v2_policy_lr_0.01_seed_2-DEMO_FILE
IMPORTANT_CONFIGS:
- env_name
- policy_lr
- seed
# 日志文件夹尾缀，若没有名为information的参数，且information的值不为"None"，那么就会用以下的值命名日志文件夹的尾缀
SHORT_NAME_SUFFIX: DEMO_FILE
```

`load_config.py`

```python
import os
import smart_logger


def init_smart_logger():
    # 设定根路径，smart_logger将会默认在根路径下新建一个日志路径来存放日志
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 两个config文件相对于跟路径的位置需要指定
    smart_logger.init_config('common_config/common_config.yaml',
                             'common_config/experiment_config.yaml',
                             base_path
                             )
```

## 2. 新建Parameter.py

新建一个`Parameter.py`的文件（可以新建一个parameter的路径，然后在该路径下新建一个`Parameter.py`，如[Parameter.py](sml_tutorial/parameter/Parameter.py)所示），这里我们需要定义一下parse函数，其定义方式与`argparser`一致。

```python
from smart_logger.parameter.ParameterTemplate import ParameterTemplate
import smart_logger
import argparse


class Parameter(ParameterTemplate):
    def __init__(self, config_path=None, debug=False, silence=False):
        super(Parameter, self).__init__(config_path, debug, silence)

    def parse(self):
      parser = argparse.ArgumentParser(description=smart_logger.experiment_config.EXPERIMENT_TARGET)
      # 开始定义参数，将所有实验用到的参数定义于此
      # （示例）参数1. 环境名
      self.env_name = 'Hopper-v2'
      parser.add_argument('--env_name', type=str, default=self.env_name,
                            help="name of the environment to run")
      # （示例）参数2. 随机种子
      self.seed = 1
      parser.add_argument('--seed', type=int, default=self.seed,
                            help="seed")
      # 其余参数
      ...
      # 定义完参数
      return parser.parse_args()
```

## 3. 在代码启动时加入几行代码

用于实例化参数与logger

1. 在main.py的最开始初始化一下`smart_logger`

```python
from common_config.load_config import init_smart_logger
# 初始化smart_logger 
init_smart_logger()
```

2. 在算法类中实例化参数、logger，并将当前参数储存下来

```python
# 标准初始化方法
from parameter.Parameter import Parameter
from smart_logger import Logger
import os

class xxx:
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
```

3. （可选）在算法类中，即可使用`self.parameter`去访问参数的值，与一般的argparser不一样的是，这个parameter类有代码提示！

```python
env_name = self.parameter.env_name
seed = self.parameter.seed
```

4. （可选）在算法类中，即可使用`self.logger`去写日志

```python
# tb_prefix是写tensorboard时的前缀，方便看tensorboard时进行变量的分组, 记录3个data1的数值，分别为1, 2, 3，记录了1个data2的数值
self.logger.add_tabular_data(tb_prefix='aaa', data1=[1, 2, 3], data2=2, date3=0.0)
# add_tabular_data可以多次调用，最后写入tensorboard并记录到文件中的是多次写入的均值
self.logger.add_tabular_data(tb_prefix='aaa', data1=[7, 8, 9], data2=10, date3=1.0)
# log_tabular只能被调用一次，这里记录了data4的数值，为10
self.logger.log_tabular(tb_prefix='bbb', key='data4', val=10)
...
# 进行数据汇总并打印结果且写入文件
self.logger.dump_tabular()
```

## 4. 将日志备份到远程

调用一行代码即可将存储下来的日志文件、发送到远程，建议在算法运行完之后再调用一遍

```python
# 将代码发送到远程机器，机器ip/port/用户名/密码定义在common_config.yam中
# success为True说明同步成功
success = self.logger.sync_log_to_remote(replace=False)
```

# 日志文件构成

每个日志目录都由两个目录五个文件构成，其中目录为

- `config`，存有当前实验的所有参数
  - `full_description.txt`表示人可以看懂的参数表示
  - `parameter.json`，在`Parameter.py`中定义的参数名
  - `run_config.json`，在`common_config`中定义的配置，同时包含git的commit id，程序运行时间，机器ip等
- `tbfile`，tensorboard记录，不过既然用上了smart_logger，就不要用tensorboard进行数据可视化了

其中文件为

- `coders.tar`，存有运行当前实验的代码，为了防止日志中文件过多，将其自动打包了
- `log.txt`，所有经由`logger`打印的数据都将在`log.txt`中储存
- `log_back.txt`，上一次日志，一般用不上
- `progress.csv`，由`add_tabular_data`, `log_tabular`等接口存下来的数据表
- `signature`，日志配置的哈希值，用于唯一确定当前配置，一般没啥用

# 启动并行实验

smart_logger提供了一个脚本来并行启动多机、多进程的实验。

试想，我们有一套代码，代码中有大量参数，而我们希望对不同的参数进行网格搜索，且运行有多个种子的实验，粗略估计一下，需要跑500次这套代码才能够跑完，而我们有三台机器，每台机器最多只能同时运行10个这样的程序进程，那么我们应该如何结合smart_logger来简便的并行启动实验呢。借助[smart_logger/scripts/generate_tmuxp_base.py](smart_logger/scripts/generate_tmuxp_base.py)将会很简单的实现这件事，一个例子如[sml_tutorial/generate_parallel_tasks.py](sml_tutorial/generate_parallel_tasks.py)所示。以下列出一些关键设置

```python
start_up_header = "python main.py "
# 4. 基础参数
parameters_base = dict(
  backing_log=True,
  seed=1
)
# 5. 遍历设置
exclusive_candidates = dict(
  env_name=['HalfCheetah-v2', 'Hopper-v2', 'Ant-v2', 'Walker2d-v2'],
  seed=[13, 17, 23, 31],
  policy_lr=[1e-4, 3e-4, 5e-5]
)
# 6. 单独设置
aligned_candidates = dict(
  information=['value_lr1', 'value_lr2', 'value_lr3'],
  value_lr=[1e-3, 1e-4, 1e-5]
)

```

其中包含了四种配置信息

- `start_up_header`，描述每个进程的入口文件
- `parameters_base`，所有任务共享的参数
- `exclusive_candidates`，网格搜索候选集合，所有可能的组合的任务都会被生成
- `aligned_candidates`，单独设置，这里每一个key对应了3个value，这三个value是对齐的，这里表示的第一种设置即information=value_lr1且value_lr=1e-3，第二种设置为information=value_lr2，且value_lr=1e-4，共有三种（与`exclusive_candidates`的网格组合不一样）。对于前面得到的所有可能的任务组合，再跟这里的三种设置遍历组合一遍，得到最终的所有任务。

这里的总任务数量为4 x 4 x 3 x 3 = 144。这里通过修改三个参数来把这些所有任务构造成执行在各个机器上的命令。

1. `MAX_PARALLEL = 10`，当前机器所能支持的最大并行程序的数量，若分配到这台机器的任务数如果大于`MAX_PARALLEL`, 命令将会以 `&&`接到前面的任务命令之后 
2. `args.total_machine_num`，机器总数，任务将会尽可能均匀的分配到这些机器上
3. `args.machine_idx`，当前机器的序号，用于在总任务中找到分配给当前机器的命令

那么我们只需要运行一下

```bash
python generate_parallel_tasks.py -tn 10 -idx 2
```

就会生成一个`run_all.json`，这里面定义了这台机器需要运行的所有指令，最后通过`tmuxp`工具，将其中的指令执行起来

```bash
tmuxp load -d run_all.json
```

那么这台机器所负责的任务就会按照预设的方式运行起来。我们可以在`logfile`中看到本次运行的所有实验的日志信息。

注意，运行`generate_parallel_tasks.py`时，会把所有命令都打印出来，通过打印信息，就能看到运行的命令是否符合我们的预期。



# 将结果可视化

我们还设计了一个前端页面，对日志数据进行展示，并绘图。启动一个网页可视化非常简单

```bash
python -m smart_logger.htmlpage
```

当然他的一些参数如下所示

```bash
usage: htmlpage.py [-h] [--workspace_path WORKSPACE_PATH] [--data_path DATA_PATH] [--user_name USER_NAME] [--password PASSWORD] [--port PORT] [--login_free]

数据可视化服务启动参数配置

optional arguments:
  -h, --help            show this help message and exit
  --workspace_path WORKSPACE_PATH, -wks WORKSPACE_PATH
                        Path to the workspace, used to saving cache data
  --data_path DATA_PATH, -d DATA_PATH
                        Path to the data
  --user_name USER_NAME, -u USER_NAME
                        user name
  --password PASSWORD, -pw PASSWORD
                        password
  --port PORT, -p PORT  Server port
  --login_free, -lf     Do not require login.
```

一般比较简便的启动方式是：

```bash
python -m smart_logger.htmlpage -wks ~/Desktop/smart_logger_cache -lf -p 7005
```

这样会使用在`~/Desktop/smart_logger_cache`的缓存文件（若无即创建），且通过`7005`端口就可以访问，且登录是不需要经过密码验证的（-lf指login-free，不需要密码）。

在进入网页时，需要把`对比绘图`中的`绘图数据加载路径 (PLOT_LOG_PATH) `改为有效的包含有日志的绝对路径，那么就可以在网页上看到结果可视化了。页面中包括四部分

- 实验列表，列了所有搜索到的日志，并可以直接下载这些日志的文件。
- 绘图参数，列出了几个重要的绘图参数，用于对日志文件过滤，对算法命名。
- 对比绘图，列出了几个绘图相关参数，并提供了一个绘图的按钮进行图像绘制。
- 表格统计，以表格的形式展示实验结果。

# 通用可视化

可视化工具不要求日志数据一定要由smart_logger储存，只需要储存的数据的格式满足一些简单的要求，数据就可以被正常读取，并可视化。

## 数据格式要求

每一个实验的数据都要存放在一个文件夹中，当然不同的实验可以不在同一级目录，我们是通过实验数据来定位实验日志的位置的。因此我们约定每个实验都需要有以下两个文件

- `progress.csv`，是一个csv的表格文件，需要保证我们如果使用`pandas`去读取这个文件不会报错，即下面的命令可以正常运行。

```python
import pandas as pd
pd.read_csv('progress.csv')
```

这是日志文件中最重要的文件，程序会通过搜索`progress.csv`来定位日志的位置。
这个表格的每一列都是一个训练过程的指标，列首标明了它的名称，之后的每一行代表了算法每一次迭代打印的数据。

- `parameter.json`，是一个json文件，它表示的是字典，并且我们需要确保我们可以通过以下命令来读取`parameter.json`

```python
import json
config = json.load(open('parameter.json', 'r'))
```

`parameter.json`需要保存到与`progress.csv`同级的位置，或者在`progress.csv`所在的文件夹的一个名为`config`的子文件夹中。
`parameter.json`储存的是算法运行的配置，我们对其中储存的东西没有硬性要求，只要他表示的是字典即可。
我们建议（没有的话程序也能运行）一个`parameter.json`中包含以下的东西

1. `env_name`，实验的任务/环境名字
2. `seed`，随机种子设置
3. `information`，实验运行时的一些额外信息，可以是实验的目的等信息

## 数据建议

smart_logger是通过`parameter.json`来区分不同的日志的，若parameter.json完全一样，会被smart_logger视作同一个日志，若用户发现日志中存在这样的数据，建议手动对`parameter.json`进行一些修改，比如增加一些key。修改json文件与csv文件的代码分别在[smart_logger/scripts/modify_config.py](smart_logger/scripts/modify_config.py), [smart_logger/scripts/modify_csv.py](smart_logger/scripts/modify_csv.py)提供。
