"""Сервер."""

import socket
import time
import logging
import select
import argparse
import re
import sys

from constants import (REQUEST_NUMBER, ACTION, TIME, USER, ACCOUNT_NAME,
                       FROM, PRESENCE, RESPONSE, ERROR, MESSAGE, MESSAGE_TEXT,
                       DEFAULT_PORT)
from utils import get_message, send_message
from logs.decos import log

logger = logging.getLogger('server')


@log
def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, nargs='?')
    parser.add_argument('-a', default='', type=str, nargs='?')
    args = parser.parse_args()

    if args.p.isdigit() and 1024 < int(args.p) < 65535:
        port = int(args.p)
    else:
        print('Неверно задан порт')
        sys.exit(1)

    if args.a:
        if re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', args.a):
            address = args.a
        else:
            print('Неверно задан адрес')
            sys.exit(1)
    else:
        address = ''
    return address, port


def process_client_message(message, client, messages_list):
    """
    Обработчик сообщений от клиентов.
    :param message: Сообщение полученное от клиента
    :param client: Клиент
    :param messages_list: Список сообщений для отправки
    :return:
    """
    logger.debug(f'Получено сообщение от {client}: {message}')
    if ACTION in message and message[ACTION] == PRESENCE \
            and TIME in message and USER in message:
        logger.debug(f'Получено presence сообщение от {client.getpeername()}')
        return send_message(client, {RESPONSE: 200})
    elif ACTION in message and message[ACTION] == MESSAGE \
            and TIME in message and FROM in message \
            and MESSAGE_TEXT in message:
        logger.debug(f'Получено сообщение от {client.getpeername()}:'
                     f' {message[MESSAGE_TEXT]}')
        return messages_list.append((message[FROM], message[MESSAGE_TEXT]))
    else:
        logger.error(f'Получено неверное сообщение. Соединение не установлено')
        return send_message(client, {RESPONSE: 400,
                                     ERROR: 'Bad request'})


def create_socket():
    """Создание соккета."""
    client_address, client_port = get_params()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((client_address, client_port))
    transport.listen(REQUEST_NUMBER)
    transport.settimeout(0.2)
    return transport


def main():
    transport = create_socket()
    clients = []
    messages_list = []

    while True:
        try:
            client, address = transport.accept()
        except OSError:
            pass
        else:
            logger.debug(f'Попытка подключения от {address}')
            clients.append(client)
        finally:
            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, err_lst, 0)
            except OSError:
                pass

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        process_client_message(get_message(client_with_message),
                                               client_with_message,
                                               messages_list)
                    except:
                        logger.error(f'Клиент {client_with_message.getpeername()} '
                                     f'отключился от сервера)')
                        clients.remove(client_with_message)

            if messages_list and send_data_lst:
                message = {
                    ACTION: MESSAGE,
                    FROM: messages_list[0][0],
                    TIME: time.time(),
                    MESSAGE_TEXT: messages_list[0][1]
                }
                del messages_list[0]
                for waiting_client in send_data_lst:
                    try:
                        send_message(waiting_client, message)
                    except:
                        logger.error(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                        waiting_client.close()
                        clients.remove(waiting_client)


if __name__ == '__main__':
    logger.debug('Запуск сервера')
    main()
