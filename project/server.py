import socket
import json
import logging
import logs.config_server_log
from constants import *
from utils import get_message, send_message, get_params

logger = logging.getLogger('server')


def process_client_message(message):
    logger.debug(f'Получено сообщение от клиента: {message}')
    if 'action' in message and message['action'] == 'presence' \
            and 'time' in message \
            and 'user' in message and message['user']['account_name'] == 'guest':
        logger.debug(f'Сообщение успешно обработано')
        return {'response': 200}
    else:
        logger.error(f'Получено неверное presence сообщение. Соединение не установлено')
        return {'response': 400,
                'error': 'Bad request'}


def main():
    client_address, client_port = get_params()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((client_address, client_port))
    transport.listen(REQUEST_NUMBER)

    while True:
        client, addr = transport.accept()
        logger.debug(f'Попытка подключения от {addr}')
        try:
            message_from_client = get_message(client)
        except (ValueError, json.decoder.JSONDecodeError):
            logger.error(f'Получено неверное presence сообщение от {addr}. Соединение не установлено')
            send_message(client, {'response': 400,
                                  'error': 'Bad request'})
            continue
        msg = process_client_message(message_from_client)
        send_message(client, msg)
        client.close()


if __name__ == '__main__':
    logger.debug('Запуск сервера')
    main()
