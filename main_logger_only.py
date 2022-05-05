from smart_logger.util_logger.logger import Logger


def main():
    logger = Logger(log_name='simple_log', logger_category='TEST')
    logger.log(122, '22', color='red', bold=False)
    data = {'a': 10, 'b': 11, 'c': 13}
    for i in range(100):
        for _ in range(10):
            for k in data:
                data[k] += 1
            logger.add_tabular_data(**data)
        logger.sync_log_to_remote()
        logger.log_tabular('a')
        logger.dump_tabular()


if __name__ == '__main__':
    main()

