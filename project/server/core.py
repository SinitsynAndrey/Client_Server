"""Сервер."""
import binascii
import socket
import logging
import select
import os
import hmac
import configparser
from descriptors import ServerPort
import threading

from constants import *
from utils import get_message, send_message
from metaclasses import ServerValidator

logger = logging.getLogger('server')


class Server(threading.Thread, metaclass=ServerValidator):
    port = ServerPort()

    config = configparser.ConfigParser()
    config.read('server.ini')

    def __init__(self, address, port, db):
        self.clients = []
        self.user_names = dict()
        self.address = address
        self.port = port
        self.db = db
        super().__init__()

    def preparation_presence_message(self, client, message):
        """Подготовка и отправка presence ответа."""
        if USER in message:
            logger.debug(f'Получено presence сообщение от {client.getpeername()}')
            if message[USER][ACCOUNT_NAME] in self.user_names:
                send_message(client, {RESPONSE: 400,
                                      ERROR: f'Имя {message[USER][ACCOUNT_NAME]} уже занято'})
                self.clients.remove(client)
                client.close()
            elif not self.db.check_user(message[USER][ACCOUNT_NAME]):
                send_message(client, {RESPONSE: 400,
                                      ERROR: f'Пользователь {message[USER][ACCOUNT_NAME]} не зарегистрирован'})
                self.clients.remove(client)
                client.close()
            else:
                random_str = binascii.hexlify(os.urandom(64))
                hash = hmac.new(self.db.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
                digest = hash.digest()
                send_message(client, {RESPONSE: 511,
                                      ALERT: random_str.decode('ascii')})
                ans = get_message(client)
                client_digest = binascii.a2b_base64(ans[ALERT])
                if RESPONSE in ans and ans[RESPONSE] == 511 and \
                        hmac.compare_digest(digest, client_digest):
                    self.user_names[message[USER][ACCOUNT_NAME]] = client
                    presence_alert = f'Добро пожаловать в чат, {message[USER][ACCOUNT_NAME]}!\n'
                    send_message(client, {RESPONSE: 200, ALERT: presence_alert})
                    client_ip, client_port = client.getpeername()
                    self.db.client_login(message[USER][ACCOUNT_NAME],
                                         client_ip,
                                         client_port,
                                         message[USER][PUBLIC_KEY])
                else:
                    send_message(client, {RESPONSE: 400,
                                          ERROR: 'Неверный пароль'})
                    self.clients.remove(client)
                    client.close()
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
                send_message(client, {RESPONSE: 200})
                self.db.modification_action_history(message[FROM], message[TO])
            else:
                send_message(client,
                             {RESPONSE: 400,
                              ERROR: f'Невозможно доставить сообщение пользователь {message[TO]} не в сети'})
        else:
            logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
            send_message(client, {RESPONSE: 400,
                                  ERROR: 'Получено некорректное сообщение'})

    def preparation_exit_message(self, client, message):
        """Обработка сообщения о выходе"""
        if ACCOUNT_NAME in message:
            logger.debug(f'Получено exit сообщение от {client.getpeername()}')
            send_message(client, {ACTION: EXIT})
            self.db.client_logout(message[ACCOUNT_NAME])
            self.clients.remove(client)
            client.close()
            del self.user_names[message[ACCOUNT_NAME]]
        else:
            logger.error(f'Получена некорректная информация о имени пользователя.')
            send_message(client, {RESPONSE: 400,
                                  ERROR: 'Получено некорректное сообщение'})

    def preparation_contacts_list(self, client, message):
        """Обработка сообщения получения списка контактов."""
        if USER in message:
            contacts = self.db.contacts_list(message[USER])
            send_message(client, {RESPONSE: 202, ALERT: contacts})

    def preparation_add_contact(self, client, message):
        """Обработка сообщения о добавления пользователя в списко контактов."""
        if USER in message and CONTACT in message:
            if message[CONTACT] in self.db.clients_list():
                self.db.add_contact(message[USER], message[CONTACT])
                send_message(client, {RESPONSE: 200,
                                      ALERT: f'Пользователь {message[CONTACT]} добавлен в список контактов'})

    def preparation_del_contact(self, client, message):
        """Обработка сообщения об удалении пользователя из списко контактов."""
        if USER in message and CONTACT in message:
            self.db.delete_contact(message[USER], message[CONTACT])
            send_message(client, {RESPONSE: 200,
                                  ALERT: f'Пользователь {message[CONTACT]} удален из списка контактов'})

    def preparation_user_request(self, client, message):
        if ACCOUNT_NAME in message:
            answer = {RESPONSE: 202,
                      ALERT: self.db.clients_list()}
            send_message(client, answer)

    def preparation_public_key_request(self, client, message):
        pub_key = self.db.get_pubkey(message[ACCOUNT_NAME])
        if pub_key:
            send_message(client, {RESPONSE: 511, ALERT: pub_key})
        else:
            send_message(client, {RESPONSE: 400,
                                  ERROR: 'Нет публичного ключа для данного пользователя'})

    def process_client_message(self, message, client):
        """Обработчик сообщений от клиентов."""
        logger.debug(f'Получено сообщение от {client.getpeername()}: {message}')
        if ACTION in message and TIME in message:
            if message[ACTION] == PRESENCE:
                self.preparation_presence_message(client, message)
            elif message[ACTION] == MESSAGE:
                self.preparation_send_message(client, message)
            elif message[ACTION] == GET_CONTACTS:
                self.preparation_contacts_list(client, message)
            elif message[ACTION] == EXIT:
                self.preparation_exit_message(client, message)
            elif message[ACTION] == ADD_CONTACT:
                self.preparation_add_contact(client, message)
            elif message[ACTION] == DEL_CONTACT:
                self.preparation_del_contact(client, message)
            elif message[ACTION] == USERS_REQUEST:
                self.preparation_user_request(client, message)
            elif message[ACTION] == PUBLIC_KEY_REQUEST:
                self.preparation_public_key_request(client, message)
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

    def run(self):
        """Основной цикл работы сервера."""
        self.create_socket()
        while True:
            try:
                client, address = self.transport.accept()
            except OSError:
                pass
            else:
                logger.debug(f'Попытка подключения от {address}')
                client.settimeout(5)
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
                            logger.error(f'Клиент уккп{client_with_message.getpeername()} '
                                         f'отключился от сервера')
                            for el in self.user_names:
                                if self.user_names[el] == client_with_message:
                                    self.db.client_logout(el)
                                    del self.user_names[el]
                                    break
                            self.clients.remove(client_with_message)
