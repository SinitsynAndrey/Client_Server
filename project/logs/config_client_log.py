import os
import sys
import logging

logger = logging.getLogger('client')


formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'client.log')

fh = logging.FileHandler(path, encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)

logger.addHandler(sh)
logger.addHandler(fh)

logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger.info('Тест работы кофигуратора логирования')
    logger.critical('Тест работы кофигуратора логирования')
