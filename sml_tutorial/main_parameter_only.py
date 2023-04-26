import os

from demo_parameter.Parameter import Parameter


def main():
    parameter = Parameter()
    parameter.set_config_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logfile',
                                           'smart_logger/parameter'))
    parameter.save_config()
    print(parameter)


if __name__ == '__main__':
    main()
