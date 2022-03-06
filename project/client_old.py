"""Client app."""

import logging
import socket
import time
import argparse
import sys
import re
from threading import Thread, RLock

import logs.config_client_log
from constants import *
from utils import get_message, send_message
from metaclasses import ClientValidator
from client_database import ClientDB

logger = logging.getLogger('client')

class Client(metaclass=ClientValidator):
    """Client app."""

    def __init__(self):
        self.server_port = ''
        self.server_address = ''
        self.client_name = ''
        self.sock_lock = RLock()
        self.contacts = []
        self.get_params()

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
            if re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\ddest{1,3}', args.a):
                self.server_address = args.a
            else:
                print('Неверно задан адрес')
                sys.exit(1)

        self.client_name = args.n

    def presence(self, transport):
        """Подготовка presence сообщения."""
        message = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
            }
        }
        logger.debug('Сформировано presence сообщение')
        send_message(transport, message)
        answer = self.processing_answer(get_message(transport))
        logger.info(answer[ALERT])

    def get_contacts(self, transport):
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.client_name
        }
        logger.debug('Сформирован запрос на получение контактов')
        send_message(transport, message)
        contacts = self.processing_answer(get_message(transport))[ALERT]
        for contact in contacts:
            self.db.add_contact(contact)

    def contact_management(self, transport):
        print('Вы можете использовать следующие команды:\n'
              'list - получение списка контактов\n'
              'add - для добавления пользователя в список контактов\n'
              'remove - для удаления пользователя из списка контактов\n'
              'back - для возврата в общее меню')
        while True:
            command = input('Введите команду:')
            if command == 'list':
                print(self.db.list_contacts())
            elif command == 'back':
                break
            elif command == 'add':
                username = input('Введите имя пользователя для добавления:\n')
                self.db.add_contact(username)
                message = {
                    ACTION: ADD_CONTACT,
                    TIME: time.time(),
                    USER: self.client_name,
                    CONTACT: username
                }
                logger.debug(f'Сформирован запрос на добавление {message[CONTACT]} в список контактов')
                with self.sock_lock:
                    send_message(transport, message)
                    answer = self.processing_answer(get_message(transport))
                if answer[RESPONSE] == 200:
                    self.db.add_contact(message[CONTACT])
                logger.info(answer)
            elif command == 'remove':
                username = input('Введите имя пользователя для удаления:\n')
                self.db.delete_contact(username)
                message = {
                    ACTION: DEL_CONTACT,
                    TIME: time.time(),
                    USER: self.client_name,
                    CONTACT: username
                }
                logger.debug(f'Сформирован запрос на удаление {message[CONTACT]} из списка контактов')
                with self.sock_lock:
                    send_message(transport, message)
                    answer = self.processing_answer(get_message(transport))
                if answer[RESPONSE] == 200:
                    self.db.delete_contact(username)
                logger.info(answer)
            else:
                print('Неверная команда.')

    def create_exit_message(self, transport):
        """Create JIM exit message."""
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            FROM: self.client_name
        }
        send_message(transport, message)

    def create_user_message(self, transport):
        """Create and send message for user."""
        print('Режим отправки сообщений.')
        while True:
            time.sleep(0.3)
            destination = input('Введите кому вы хотите отправить сообщение'
                                ' или back для возврата: \n')

            if destination != 'back':
                text_message = input('Введите сообщение:')
                message = {
                    ACTION: MESSAGE,
                    TIME: time.time(),
                    FROM: self.client_name,
                    TO: destination,
                    MESSAGE_TEXT: text_message
                }
                try:
                    send_message(transport, message)
                    logger.debug(f'Отправлено сообщение: {message} пользователю {message[TO]}')
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.error(f'Соединение с сервером {transport.getpeername()} было потеряно.')
                    sys.exit(1)
            else:
                break

    @staticmethod
    def call_help():
        print('Вы в интерактивном чате. Для управления '
              'используйте следующие команды:\n'
              'help - вызов помощи\n'
              'message - отправка сообщения\n'
              'contacts -работа со списком контактов\n'
              'users - получение списка пользователей в сети\n'
              'exit - выход из чата')

    def client_interface(self, transport):
        """User interaction."""
        self.call_help()
        while True:
            command = input('Введите команду или help для вызова помощи:\n')
            if command == 'message':
                self.create_user_message(transport)
            elif command == 'contacts':
                self.contact_management(transport)
            elif command == 'exit':
                self.create_exit_message(transport)
                logger.info(f'Выход осуществлен')
                time.sleep(0.5)
                break
            elif command == 'help':
                self.call_help()

    @staticmethod
    def processing_answer(answer):
        """Обработка ответа сервера на presence."""
        logger.debug(f'Получен ответ от сервера: {answer}')
        if RESPONSE in answer:
            if answer[RESPONSE] == 200:
                return answer
            elif answer[RESPONSE] == 206:
                return answer
            elif answer[RESPONSE] == 400:
                logger.critical(f'{answer[ERROR]}')
                sys.exit(1)
        else:
            logger.critical(f'Неверный ответ сервера')
            sys.exit(1)

    @staticmethod
    def message_from_server(transport):
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

        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.connect((self.server_address, self.server_port))
        except ConnectionRefusedError:
            logger.critical(f'Не удалось подключиться к {self.server_address} {self.server_port}')
            sys.exit(1)
        logger.debug(f'Подключение к {self.server_address} {self.server_port}')
        if not self.client_name:
            self.client_name = input("Введите ваш ник:")
        self.presence(transport)
        self.db = ClientDB(self.client_name)
        self.get_contacts(transport)

        TR_listen = Thread(target=self.message_from_server, args=(transport,))
        TR_listen.daemon = True
        TR_listen.start()

        TR_send = Thread(target=self.client_interface, args=(transport,))
        TR_send.daemon = True
        TR_send.start()

        while True:
            if TR_send.is_alive() and TR_listen.is_alive():
                continue
            break

    def run_client(self):
        self.main()
        input()


if __name__ == '__main__':
    client = Client()
    client.run_client()
