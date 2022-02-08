import json
import sys
import re
import argparse
from constants import *
import traceback
import logging
import logs.config_server_log
import logs.config_client_log
from logs.decos import log


TRACE = traceback.format_stack()

if 'client' in TRACE[0]:
    logger = logging.getLogger('client')
else:
    logger = logging.getLogger('server')

@log
def get_message(client):

    encode_response = client.recv(MAX_PACKAGES_LENGTH)
    if isinstance(encode_response, bytes):
        decode_response = encode_response.decode(ENCODING)
        response = json.loads(decode_response)
        if isinstance(response, dict):
            return response
        else:
            raise ValueError
    else:
        raise ValueError


@log
def send_message(client, msg):
    """Отправка сообщения."""
    try:
        json_response = json.dumps(msg)
    except json.JSONDecodeError:
        logger.critical(f'Сообщение: {msg} не удалось'
                        f' преобразовать в JSON строку')
    encode_response = json_response.encode(ENCODING)
    client.send(encode_response)


if __name__ == '__main__':
    print(get_params())
