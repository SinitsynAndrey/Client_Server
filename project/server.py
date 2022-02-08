"""Сервер."""

import socket
import logging
import select
import argparse
import re
import sys

from constants import (REQUEST_NUMBER, ACTION, TIME, USER, ACCOUNT_NAME,
                       FROM, PRESENCE, RESPONSE, ERROR, MESSAGE, MESSAGE_TEXT,
                       DEFAULT_PORT, TO, ALERT, EXIT)
from utils import get_message, send_message
from logs.decos import log

logger = logging.getLogger('server')


def get_params():
    """Функция считывает параметры запуска.
    -p - порт сервера
    -a - ip-адрес сервера
    """
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


def preparation_presence_message(client, message, user_names):
    """Подготовка и отправка presence ответа."""
    if USER in message:
        logger.debug(f'Получено presence сообщение от {client.getpeername()}')
        if message[USER][ACCOUNT_NAME] not in user_names:
            user_names[message[USER][ACCOUNT_NAME]] = client
            presence_alert = f'Добро пожаловать в чат, {message[USER][ACCOUNT_NAME]}!\n'
            send_message(client, {RESPONSE: 200, ALERT: presence_alert})
        else:
            send_message(client, {RESPONSE: 400, ERROR: f'Имя {message[USER][ACCOUNT_NAME]} уже занято'})
    else:
        logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
        send_message(client, {RESPONSE: 400,
                              ERROR: 'Некорректная информация о имени пользователя. Соединение не установлено'})


def preparation_send_message(client, message, user_names):
    """Обработка и отправка сообщения от клиента к клиенту."""

    if FROM in message and TO in message and MESSAGE_TEXT in message:
        logger.debug(f'Получено сообщение от пользователя{message[FROM]}: {message[MESSAGE_TEXT]}')
        if message[TO] in user_names:
            send_message(user_names[message[TO]], message)
        else:
            send_message(client,
                         {RESPONSE: 400,
                          ERROR: f'Невозможно доставить сообщение пользователь {message[TO]} не в сети'})
    else:
        logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
        send_message(client, {RESPONSE: 400,
                              ERROR: 'Получено некорректное сообщение'})


def preparation_exit_message(client, message, user_names, clients):
    """Обработка сообщения о выходе"""
    if FROM in message:
        logger.debug(f'Получено exit сообщение от {client.getpeername()}')
        send_message(client, {ACTION: EXIT})
        clients.remove(client)
        client.close()
        del user_names[message[FROM]]
    else:
        logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
        send_message(client, {RESPONSE: 400,
                              ERROR: 'Получено некорректное сообщение'})


def process_client_message(message, client, user_names, clients):
    """Обработчик сообщений от клиентов."""
    logger.debug(f'Получено сообщение от {client.getpeername()}: {message}')
    if ACTION in message and TIME in message:
        if message[ACTION] == PRESENCE:
            preparation_presence_message(client, message, user_names)
        elif message[ACTION] == MESSAGE:
            preparation_send_message(client, message, user_names)
        elif message[ACTION] == EXIT:
            preparation_exit_message(client, message, user_names, clients)
    else:
        logger.error(f'Получено неверное сообщение. Соединение не установлено')
        send_message(client, {RESPONSE: 400, ERROR: 'Bad request'})


def create_socket():
    """Создание соккета."""
    client_address, client_port = get_params()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((client_address, client_port))
    transport.listen(REQUEST_NUMBER)
    transport.settimeout(0.2)
    return transport


def main():
    """Основной цикл работы сервера."""
    transport = create_socket()
    clients = []
    user_names = dict()

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
                                               user_names,
                                               clients)
                    except:
                        logger.error(f'Клиент {client_with_message.getpeername()} '
                                     f'отключился от сервера)')
                        clients.remove(client_with_message)


if __name__ == '__main__':
    logger.info('Запуск сервера')
    main()
