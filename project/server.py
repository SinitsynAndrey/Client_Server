"""Сервер."""

import socket
import logging
import select
import argparse
import re
import sys
from descriptors import ServerPort

from constants import (REQUEST_NUMBER, ACTION, TIME, USER, ACCOUNT_NAME,
                       FROM, PRESENCE, RESPONSE, ERROR, MESSAGE, MESSAGE_TEXT,
                       DEFAULT_PORT, TO, ALERT, EXIT)
from utils import get_message, send_message
import logs.config_server_log
from metaclasses import ServerValidator

logger = logging.getLogger('server')


class Server(metaclass=ServerValidator):

    port = ServerPort()

    def __init__(self):
        self.clients = []
        self.user_names = dict()

    def get_params(self):
        """Функция считывает параметры запуска.
        -p - порт сервера
        -a - ip-адрес сервера
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=DEFAULT_PORT, nargs='?')
        parser.add_argument('-a', default='', type=str, nargs='?')
        args = parser.parse_args()

        if args.a:
            if re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', args.a):
                address = args.a
            else:
                print('Неверно задан адрес')
                sys.exit(1)
        else:
            address = ''
        self.address = address
        self.port = args.p

    def preparation_presence_message(self, client, message):
        """Подготовка и отправка presence ответа."""
        if USER in message:
            logger.debug(f'Получено presence сообщение от {client.getpeername()}')
            if message[USER][ACCOUNT_NAME] not in self.user_names:
                self.user_names[message[USER][ACCOUNT_NAME]] = client
                presence_alert = f'Добро пожаловать в чат, {message[USER][ACCOUNT_NAME]}!\n'
                send_message(client, {RESPONSE: 200, ALERT: presence_alert})
            else:
                send_message(client, {RESPONSE: 400, ERROR: f'Имя {message[USER][ACCOUNT_NAME]} уже занято'})
        else:
            logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
            send_message(client, {RESPONSE: 400,
                                  ERROR: 'Некорректная информация о имени пользователя. Соединение не установлено'})

    def preparation_send_message(self, client, message):
        """Обработка и отправка сообщения от клиента к клиенту."""

        if FROM in message and TO in message and MESSAGE_TEXT in message:
            logger.debug(f'Получено сообщение от пользователя{message[FROM]}: {message[MESSAGE_TEXT]}')
            if message[TO] in self.user_names:
                send_message(self.user_names[message[TO]], message)
            else:
                send_message(client,
                             {RESPONSE: 406,
                              ERROR: f'Невозможно доставить сообщение пользователь {message[TO]} не в сети'})
        else:
            logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
            send_message(client, {RESPONSE: 400,
                                  ERROR: 'Получено некорректное сообщение'})

    def preparation_exit_message(self, client, message):
        """Обработка сообщения о выходе"""
        if FROM in message:
            logger.debug(f'Получено exit сообщение от {client.getpeername()}')
            send_message(client, {ACTION: EXIT})
            self.clients.remove(client)
            client.close()
            del self.user_names[message[FROM]]
        else:
            logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
            send_message(client, {RESPONSE: 400,
                                  ERROR: 'Получено некорректное сообщение'})

    def process_client_message(self, message, client):
        """Обработчик сообщений от клиентов."""
        logger.debug(f'Получено сообщение от {client.getpeername()}: {message}')
        if ACTION in message and TIME in message:
            if message[ACTION] == PRESENCE:
                self.preparation_presence_message(client, message)
            elif message[ACTION] == MESSAGE:
                self.preparation_send_message(client, message)
            elif message[ACTION] == EXIT:
                self.preparation_exit_message(client, message)
        else:
            logger.error(f'Получено неверное сообщение. Соединение не установлено')
            send_message(client, {RESPONSE: 400, ERROR: 'Bad request'})

    def create_socket(self):
        """Создание соккета."""
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.address, self.port))
        transport.settimeout(0.2)

        self.transport = transport
        self.transport.listen(REQUEST_NUMBER)

    def main(self):
        """Основной цикл работы сервера."""

        while True:
            try:
                client, address = self.transport.accept()
            except OSError:
                pass
            else:
                logger.debug(f'Попытка подключения от {address}')
                self.clients.append(client)
            finally:
                recv_data_lst = []
                err_lst = []
                try:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, err_lst, 0)
                except OSError:
                    pass

                if recv_data_lst:
                    for client_with_message in recv_data_lst:
                        try:
                            self.process_client_message(get_message(client_with_message), client_with_message)
                        except:
                            logger.error(f'Клиент {client_with_message.getpeername()} '
                                         f'отключился от сервера')
                            for el in self.user_names:
                                if self.user_names[el] == client_with_message:
                                    del self.user_names[el]
                                    break
                            self.clients.remove(client_with_message)

    def run_server(self):
        self.get_params()
        self.create_socket()
        self.main()


if __name__ == '__main__':
    logger.info('Запуск сервера')
    server = Server()
    server.run_server()
