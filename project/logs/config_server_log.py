import os
import sys
import logging
import logging.handlers

logger = logging.getLogger('server')


formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')
formatter_stdout = logging.Formatter('%(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'server.log')

fh = logging.handlers.TimedRotatingFileHandler(path, encoding='utf8', interval=1, when='H')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.INFO)
sh.setFormatter(formatter_stdout)

logger.addHandler(fh)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger.info('Тест работы кофигуратора логирования')
    logger.critical('Тест работы кофигуратора логирования')
