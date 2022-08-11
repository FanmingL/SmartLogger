from smart_logger.parameter.ParameterTemplate import ParameterTemplate
import smart_logger
import argparse


class Parameter(ParameterTemplate):
    def __init__(self, config_path=None, debug=False, silence=False):
        super(Parameter, self).__init__(config_path, debug, silence)

    def parse(self):
        parser = argparse.ArgumentParser(description=smart_logger.experiment_config.EXPERIMENT_TARGET)

        self.env_name = 'Hopper-v2'
        parser.add_argument('--env_name', type=str, default=self.env_name, metavar='N',
                            help="name of the environment to run")

        self.seed = 1
        parser.add_argument('--seed', type=int, default=self.seed, metavar='N',
                            help="random seed")

        self.policy_lr = 3e-4
        parser.add_argument('--policy_lr', type=float, default=self.policy_lr, metavar='N',
                            help="learning rate of the policy.")

        self.value_lr = 1e-4
        parser.add_argument('--value_lr', type=float, default=self.value_lr, metavar='N',
                            help="learning rate of the value function.")

        self.backing_log = False
        parser.add_argument('--backing_log', action='store_true',
                            help='whether backing up the log files to a remote machine.')

        self.information = 'TEST'
        parser.add_argument('--information', type=str, default=self.information, metavar='N',
                            help="log file suffix")

        return parser.parse_args()
