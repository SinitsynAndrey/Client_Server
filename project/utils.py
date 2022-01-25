import json
import sys
import re
from constants import *
import traceback
from logs.decos import log
import logs.config_server_log


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
    json_response = json.dumps(msg)
    encode_response = json_response.encode(ENCODING)
    client.send(encode_response)


@log
def get_params():
    if '-p' in sys.argv:
        if len(sys.argv) > sys.argv.index('-p') + 1 \
                and sys.argv[sys.argv.index('-p') + 1].isdigit() \
                and 1024 < int(sys.argv[sys.argv.index('-p') + 1]) < 65535:
            port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            print('Неверно задан порт')
            sys.exit(1)
    else:
        port = DEFAULT_PORT

    if '-a' in sys.argv:
        if len(sys.argv) > sys.argv.index('-a') + 1 \
                and re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', sys.argv[sys.argv.index('-a') + 1]):
            adress = sys.argv[sys.argv.index('-a') + 1]
        else:
            print('Неверно задан адрес')
            sys.exit(1)
    else:
        adress = ''
    return adress, port
