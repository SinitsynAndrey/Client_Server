import logging
import socket
import time
import argparse
import sys
import re
from threading import Thread

from constants import (ACTION, TIME, USER, ACCOUNT_NAME, ERROR, EXIT,
                       FROM, PRESENCE, RESPONSE, MESSAGE, MESSAGE_TEXT,
                       DEFAULT_PORT, DEFAULT_SERVER_ADDRESS, TO, ALERT)
from utils import get_message, send_message
from logs.decos import log


logger = logging.getLogger('client')


def get_params():
    """Функция считывает параметры запуска.
       -p - порт сервера
       -a - ip-адрес сервера
       -n - никнэйм
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, nargs='?')
    parser.add_argument('-a', default=DEFAULT_SERVER_ADDRESS, nargs='?')
    parser.add_argument('-n', default=None, nargs='?')
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

    name = args.n

    return address, port, name


def preparation_presence_message(account_name):
    """Подготовка presence сообщения."""
    if not account_name:
        account_name = input("Введите ваш ник:")
    message = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug('Сформировано presence сообщение')
    return message


def preparation_and_send_messages(transport, name):
    """Функция создания и отправки сообщений."""
    while True:
        dest = input('Введите имя кому вы хотите отправить сообщение или "exit" для выхода:\n')
        if dest == 'exit':
            message = {
                ACTION: EXIT,
                TIME: time.time(),
                FROM: name
            }
            send_message(transport, message)
            logger.info(f'Выход осуществлен')
            time.sleep(0.5)
            break
        text_message = input('Введите сообщение:')
        message = {
            ACTION: MESSAGE,
            TIME: time.time(),
            FROM: name,
            TO: dest,
            MESSAGE_TEXT: text_message
        }
        try:
            send_message(transport, message)
            logger.debug(f'Отправлено сообщение: {message} пользователю {message[TO]}')
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            logger.error(f'Соединение с сервером {transport.getpeername()} было потеряно.')
            break


def processing_answer(answer):
    """Обработка ответа сервера на presence."""
    logger.debug(f'Получен ответ от сервера: {answer}')
    if RESPONSE in answer:
        if answer[RESPONSE] == 200:
            logger.info(f'{answer[ALERT]}')
        elif answer[RESPONSE] == 400:
            logger.critical(f'{answer[ERROR]}')
            sys.exit(1)
    else:
        logger.critical(f'Неверный ответ сервера')
        sys.exit(1)


def message_from_server(transport):
    """Прием сообщений от сервера"""
    while True:
        message = get_message(transport)
        if ACTION in message and message[ACTION] == MESSAGE and \
                FROM in message and MESSAGE_TEXT in message:
            print(f'{message[FROM]}: {message[MESSAGE_TEXT]}')
        elif ACTION in message and message[ACTION] == EXIT:
            break
        else:
            logger.error(f'Получено некорректное сообщение от сервера: {message}')
            break


def main():
    """Основной цикл работы клиента."""
    server_address, server_port, user_name = get_params()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        transport.connect((server_address, server_port))
    except ConnectionRefusedError:
        logger.critical(f'Не удалось подключиться к {server_address} {server_port}')
        sys.exit(1)
    logger.debug(f'Подключение к {server_address} {server_port}')
    send_message(transport, preparation_presence_message(user_name))
    processing_answer(get_message(transport))

    TR_listen = Thread(target=message_from_server, args=(transport, ))
    TR_listen.daemon = True
    TR_listen.start()

    TR_send = Thread(target=preparation_and_send_messages, args=(transport, user_name))
    TR_send.daemon = True
    TR_send.start()

    while True:
        if TR_send.is_alive() and TR_listen.is_alive():
            continue
        break


if __name__ == '__main__':
    main()
