"""Декораторы логирования """

import traceback
import logging


TRACE = traceback.format_stack()

if 'client' in TRACE[0]:
    LOGGER = logging.getLogger('client')
else:
    LOGGER = logging.getLogger('server')


def log(func_to_log):
    """Функция декоратор"""

    def wrap(*args, **kwargs):
        res = func_to_log(*args, **kwargs)
        trace = traceback.format_stack()
        LOGGER.debug(f' Вызвана функция {func_to_log.__name__} c аргументами {args}, {kwargs}'
                     f' из модуля {func_to_log.__module__}.'
                     f' Вызов из функции {trace[0].split()[-1]}')
        return res

    return wrap
