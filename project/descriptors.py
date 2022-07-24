"""Descriptors."""

import logging
import sys
import logs.config_client_log
import logs.config_server_log
from logs.decos import log

if 'server' in sys.argv[0]:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


class ServerPort:
    """Port validation descriptor."""
    def __set__(self, instance, value):
        if type(value) != int or not 1024 < value < 65535:
            logger.error('Не удалось запустить сервер! Неверно задан порт.')
            sys.exit(1)
        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr

