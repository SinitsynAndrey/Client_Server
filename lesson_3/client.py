import socket
import time
from constants import *
from utils import get_params, get_message, send_message


def preparation_message(account_name='guest'):
    return {
        'action': 'presence',
        'time': time.time(),
        'user': {
            'account_name': account_name
        }
    }


def processing_answer(answer):
    if 'response' in answer and answer['response'] == 200:
        return 'Соединение установлено'
    return 'Connection error'


def main():
    server_adress, server_port = get_params()
    if not server_adress:
        server_adress = DEFAULT_SERVER_ADRESS
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        transport.connect((server_adress, server_port))
    except ConnectionRefusedError:
        return print('Неверные параметры подключения')
    msg = preparation_message()
    send_message(transport, msg)
    answer_by_server = get_message(transport)
    print(processing_answer(answer_by_server))
    transport.close()


if __name__ == '__main__':
    main()
