import logging
import socket
import time
import argparse
import sys
import re

from constants import (ACTION, TIME, USER, ACCOUNT_NAME,
                       FROM, PRESENCE, RESPONSE, MESSAGE, MESSAGE_TEXT,
                       DEFAULT_PORT, DEFAULT_SERVER_ADDRESS)
from utils import get_message, send_message
from logs.decos import log


logger = logging.getLogger('client')


@log
def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, nargs='?')
    parser.add_argument('-a', default=DEFAULT_SERVER_ADDRESS, nargs='?')
    parser.add_argument('-m', required=True)
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

    if args.m not in ('listen', 'send'):
        logger.error(f'Необходимо указать режим работы клиента.'
                     f'Возможные варианты: send listen')
    else:
        mode = args.m
    return address, port, mode


def preparation_presence_message(account_name='guest'):
    message = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug('Сформировано presence сообщение')
    return message


def create_message():
    text_message = input('Введите сообщение для отправки. '
                         'Для выхода введите: "exit"')
    message = {
        ACTION: MESSAGE,
        TIME: time.time(),
        FROM: 'guest',
        MESSAGE_TEXT: text_message
    }
    return message


def processing_answer(answer):
    """Обработка ответа сервера на presence."""
    logger.debug(f'Получен ответ от сервера: {answer}')
    if RESPONSE in answer:
        if answer[RESPONSE] == 200:
            logger.info('Соединение с сервером установлено.')
            return True
        elif answer[RESPONSE] == 400:
            logger.critical(f'Сервер вернул ошибку. Error 400')
            sys.exit(1)
    logger.critical(f'Неверный ответ сервера')
    sys.exit(1)


def message_from_server(message):
    if ACTION in message and message[ACTION] == MESSAGE and \
            FROM in message and MESSAGE_TEXT in message:
        print(f'{message[FROM]}: {message[MESSAGE_TEXT]}')
    else:
        logger.error(f'Получено некорректное сообщение от сервера: {message}')


def main():
    server_address, server_port, mode = get_params()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        transport.connect((server_address, server_port))
    except ConnectionRefusedError:
        logger.critical(f'Не удалось подключиться к {server_address} {server_port}')
        sys.exit(1)
    logger.debug(f'Подключение к {server_address} {server_port}')
    msg = preparation_presence_message()
    send_message(transport, msg)
    answer_by_server = processing_answer(get_message(transport))

    if answer_by_server:
        if mode == 'send':
            print('Режим работы - отправка сообщений.')
        else:
            print('Режим работы - приём сообщений.')

        while True:
            if mode == 'send':
                try:
                    message = create_message()
                    if message[MESSAGE_TEXT] == 'exit':
                        transport.close()
                        logger.debug(f'Соединение разорвано клиентом')
                        sys.exit(1)
                    send_message(transport, message)
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)

            if mode == 'listen':
                try:
                    message_from_server(get_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)


if __name__ == '__main__':
    main()
