import os


def main():
    csv_name = 'progress.csv'
    modifies = {
        'EpRetTest': 'EpRetDirectTransfer'
    }
    script_path = os.path.dirname(os.path.abspath(__file__))
    for root, dir_name, file_name in os.walk(script_path):
        for f_name in file_name:
            if f_name == csv_name:
                print(f'{os.path.join(root,f_name)}')
                full_path = os.path.join(root, f_name)
                with open(full_path, 'r') as f:
                    header = f.readline()
                    splited = header.split(',')
                    idx_dict = dict()
                    for ind, item in enumerate(splited):
                        for k, v in modifies.items():
                            if k == item:
                                idx_dict[k] = ind
                            if v == item:
                                idx_dict[v] = ind
                    if len(idx_dict) == 1:
                        continue
                    else:
                        with open(full_path + '123', 'w') as f_w:
                            f_w.write(header)
                            for line in f:
                                items = line.split(',')
                                for k, v in modifies.items():
                                    items[idx_dict[k]] = items[idx_dict[v]]
                                line = ','.join(items)
                                f_w.write(line)
                        os.system(f'mv {full_path}123 {full_path}')


if __name__ == '__main__':
    main()
