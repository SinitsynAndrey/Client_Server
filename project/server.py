"""Сервер."""

import socket
import logging
import select
import argparse
import os
import re
import sys
import configparser
from descriptors import ServerPort
from server_database import ServerDB
import threading

from constants import *
from utils import get_message, send_message
import logs.config_server_log
from metaclasses import ServerValidator

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow

logger = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerValidator):
    port = ServerPort()

    config = configparser.ConfigParser()
    config.read('server.ini')

    def __init__(self, config, db):
        self.clients = []
        self.user_names = dict()
        self.config = config
        self.address, self.port, self.db_path = self.get_params()
        self.db = db
        super().__init__()

    def get_params(self):
        """Функция считывает параметры запуска.
        -p - порт сервера
        -a - ip-адрес сервера
        """

        default_port = self.config['SETTINGS']['default_port']
        default_address = self.config['SETTINGS']['listen_address']

        db_path = os.path.join(self.config['SETTINGS']['Database_path'],
                               self.config['SETTINGS']['Database_file'])

        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=default_port, nargs='?')
        parser.add_argument('-a', default=default_address, type=str, nargs='?')
        args = parser.parse_args()

        if args.a:
            if not re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', args.a):
                logger.error('Неверно задан адрес')
                sys.exit(1)

        address = args.a
        port = int(args.p)
        return address, port, db_path

    def preparation_presence_message(self, client, message):
        """Подготовка и отправка presence ответа."""
        global new_connection
        if USER in message:
            logger.debug(f'Получено presence сообщение от {client.getpeername()}')
            if message[USER][ACCOUNT_NAME] not in self.user_names:
                self.user_names[message[USER][ACCOUNT_NAME]] = client
                presence_alert = f'Добро пожаловать в чат, {message[USER][ACCOUNT_NAME]}!\n'
                send_message(client, {RESPONSE: 200, ALERT: presence_alert})
                with conflag_lock:
                    new_connection = True
                client_ip, client_port = client.getpeername()
                self.db.client_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
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
                self.db.modification_action_history(message[FROM], message[TO])
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
        global new_connection
        if FROM in message:
            logger.debug(f'Получено exit сообщение от {client.getpeername()}')
            send_message(client, {ACTION: EXIT})
            self.db.client_logout(message[FROM])
            self.clients.remove(client)
            client.close()
            del self.user_names[message[FROM]]
            with conflag_lock:
                new_connection = True
        else:
            logger.error(f'Получена некорректная информация о имени пользователя. Соединение не установлено')
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
            if message[CONTACT] in self.db.contacts_list(message[USER]):
                self.db.delete_contact(message[USER], message[CONTACT])
                send_message(client, {RESPONSE: 200,
                                      ALERT: f'Пользователь {message[CONTACT]} удален из списка контактов'})
            else:
                send_message(client, {RESPONSE: 206,
                                      ALERT: f'Пользователь {message[CONTACT]} отсутствует в списке контактов'})

    def preparation_user_request(self, client, message):
        if ACCOUNT_NAME in message:
            answer = {RESPONSE: 202,
                      ALERT: self.db.clients_list()}
            send_message(client, answer)

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


def create_gui(config, db):
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(db))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(db))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(db))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        db_path = os.path.join(config['SETTINGS']['Database_path'],
                               config['SETTINGS']['Database_file'])
        config_window = ConfigWindow()
        config_window.db_path.insert(db_path)
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


def run_server():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    database = ServerDB(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    server = Server(config, database)
    server.daemon = True
    server.start()

    create_gui(config, database)


if __name__ == '__main__':
    logger.info('Запуск сервера')
    run_server()
