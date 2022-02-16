import logging
import socket
import time
import argparse
import sys
import re
from threading import Thread


import logs.config_client_log
from constants import (ACTION, TIME, USER, ACCOUNT_NAME, ERROR, EXIT,
                       FROM, PRESENCE, RESPONSE, MESSAGE, MESSAGE_TEXT,
                       DEFAULT_PORT, DEFAULT_SERVER_ADDRESS, TO, ALERT)
from utils import get_message, send_message
from metaclasses import ClientValidator

logger = logging.getLogger('client')


class Client(metaclass=ClientValidator):

    def __init__(self):
        self.server_port = ''
        self.server_address = ''
        self.client_name = ''

    def get_params(self):
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

        if type(args.p) == int and 1024 < int(args.p) < 65535:
            self.server_port = args.p
        else:
            print('Неверно задан порт')
            sys.exit(1)

        if args.a:
            if re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', args.a):
                self.server_address = args.a
            else:
                print('Неверно задан адрес')
                sys.exit(1)
        else:
            self.server_address = ''

        self.client_name = args.n

    def preparation_presence_message(self):
        """Подготовка presence сообщения."""
        message = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
            }
        }
        logger.debug('Сформировано presence сообщение')
        return message

    def preparation_and_send_messages(self, transport):
        """Функция создания и отправки сообщений."""
        while True:
            dest = input('Введите имя кому вы хотите отправить сообщение или "exit" для выхода:\n')
            if dest == 'exit':
                message = {
                    ACTION: EXIT,
                    TIME: time.time(),
                    FROM: self.client_name
                }
                send_message(transport, message)
                logger.info(f'Выход осуществлен')
                time.sleep(0.5)
                break
            text_message = input('Введите сообщение:')
            message = {
                ACTION: MESSAGE,
                TIME: time.time(),
                FROM: self.client_name,
                TO: dest,
                MESSAGE_TEXT: text_message
            }
            try:
                send_message(transport, message)
                logger.debug(f'Отправлено сообщение: {message} пользователю {message[TO]}')
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                logger.error(f'Соединение с сервером {transport.getpeername()} было потеряно.')
                break

    def processing_answer(self, answer):
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

    def message_from_server(self, transport):
        """Прием сообщений от сервера"""
        while True:
            message = get_message(transport)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    FROM in message and MESSAGE_TEXT in message:
                print(f'{message[FROM]}: {message[MESSAGE_TEXT]}')
            elif ACTION in message and message[ACTION] == EXIT:
                break
            elif RESPONSE in message and message[RESPONSE] == 406:
                logger.error(f'{message[ERROR]}')
            else:
                logger.error(f'Получено некорректное сообщение от сервера: {message}')
                break

    def main(self):
        """Основной цикл работы клиента."""
        self.get_params()
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            transport.connect((self.server_address, self.server_port))
        except ConnectionRefusedError:
            logger.critical(f'Не удалось подключиться к {self.server_address} {self.server_port}')
            sys.exit(1)
        logger.debug(f'Подключение к {self.server_address} {self.server_port}')
        if not self.client_name:
            self.client_name = input("Введите ваш ник:")
        send_message(transport, self.preparation_presence_message())
        self.processing_answer(get_message(transport))

        TR_listen = Thread(target=self.message_from_server, args=(transport, ))
        TR_listen.daemon = True
        TR_listen.start()

        TR_send = Thread(target=self.preparation_and_send_messages, args=(transport, ))
        TR_send.daemon = True
        TR_send.start()

        while True:
            if TR_send.is_alive() and TR_listen.is_alive():
                continue
            break

    def run_client(self):
        self.get_params()
        self.main()


if __name__ == '__main__':
    client = Client()
    client.run_client()

