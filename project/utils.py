import json
import sys
import logging
from constants import *
from logs.decos import log

if 'server' in sys.argv[0]:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


@log
def get_message(client):
    """Get and decode message"""
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
    """Encode and send message."""
    try:
        json_response = json.dumps(msg)
    except json.JSONDecodeError:
        logger.critical(f'Сообщение: {msg} не удалось'
                        f' преобразовать в JSON строку')
    encode_response = json_response.encode(ENCODING)
    client.send(encode_response)
