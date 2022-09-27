import json
import os


def main():
    config_name = 'parameter.json'
    modifies = {
        'alg_name': 'ppo_transfer'
    }
    script_path = os.path.dirname(os.path.abspath(__file__))
    for root, dir_name, file_name in os.walk(script_path, followlinks=True):
        for f_name in file_name:
            if f_name == config_name:
                print(f'{os.path.join(root,f_name)}')
                full_path = os.path.join(root, f_name)
                try:
                    config = json.load(open(full_path, 'r'))
                    for k, v in modifies.items():
                        if k in config:
                            config[k] = v
                    with open(full_path, 'w') as f:
                        json.dump(config, f)
                except Exception as e:
                    print(f'reading {root}, {dir_name}')
    pass


if __name__ == '__main__':
    main()