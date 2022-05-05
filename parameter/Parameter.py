from smart_logger.parameter.ParameterTemplate import ParameterTemplate
from smart_logger.common.experiment_config import *
import argparse


class Parameter(ParameterTemplate):
    def __init__(self, config_path=None, debug=False):
        super(Parameter, self).__init__(config_path, debug)

    def parse(self):
        parser = argparse.ArgumentParser(description=EXPERIMENT_TARGET)

        self.env_name = 'Hopper-v2'
        parser.add_argument('--env_name', type=str, default=self.env_name, metavar='N',
                            help="name of the environment to run")

        self.sac_update_interval = 1
        parser.add_argument('--sac_update_interval', type=int, default=self.sac_update_interval, metavar='N',
                            help="sample number per sac update.")

        self.policy_lr = 3e-4
        parser.add_argument('--policy_lr', type=float, default=self.policy_lr, metavar='N',
                            help="learning rate of the policy.")

        self.backing_log = False
        parser.add_argument('--backing_log', action='store_true',
                            help='whether backing up the log files to a remote machine.')

        self.seed = 1
        parser.add_argument('--seed', type=int, default=self.seed, metavar='N',
                            help="seed")

        self.information = "None"
        parser.add_argument('--information', type=str, default=self.information, metavar='N',
                            help="information")

        return parser.parse_args()


if __name__ == '__main__':
    def main():
        parameter = Parameter()
        print(parameter)
    main()