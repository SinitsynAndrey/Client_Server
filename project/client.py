import logging
import logs.config_client_log
import socket
import time
from constants import *
from utils import get_params, get_message, send_message

logger = logging.getLogger('client')

def preparation_message(account_name='guest'):
    message = {
        'action': 'presence',
        'time': time.time(),
        'user': {
            'account_name': account_name
        }
    }
    logger.debug('Сформировано presence сообщение')
    return message


def processing_answer(answer):
    if 'response' in answer and answer['response'] == 200:
        return logger.info('Соединение с сервером установлено.')
    return logger.error(f'Не удалось подключиться к серверу. Ошибка {answer["response"]}')



def main():
    server_address, server_port = get_params()
    if not server_address:
        server_address = DEFAULT_SERVER_ADRESS
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        transport.connect((server_address, server_port))
        logger.debug(f'Подключение к {server_address} {server_port}')
    except ConnectionRefusedError:
        return logger.critical(f'Не удалось подключиться к {server_address} {server_port}')
    msg = preparation_message()
    send_message(transport, msg)
    answer_by_server = get_message(transport)
    processing_answer(answer_by_server)
    transport.close()


if __name__ == '__main__':
    main()
