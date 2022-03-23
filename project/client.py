import sys
import os
import argparse
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox

from constants import *
from errors import ServerError
from logs.decos import log
from Cryptodome.PublicKey import RSA
from client.client_database import ClientDB
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from client.main_window import ClientMainWindow

logger = logging.getLogger('client')


class Client:
    """Client application initialization."""
    def __init__(self):
        self.server_address = None
        self.server_port = None
        self.client_name = None
        self.client_password = None

        self.arg_parser()

        self.client_app = QApplication(sys.argv)

        if not (self.client_name and self.client_password):
            start_dialog = UserNameDialog()
            self.client_app.exec_()
            if start_dialog.ok_pressed:
                self.client_name = start_dialog.client_name.text()
                self.client_password = start_dialog.client_password.text()
            else:
                sys.exit(0)

        logger.debug(
            f'Запущен клиент с парамертами: адрес сервера: {self.server_address} , '
            f'порт: {self.server_port}, имя пользователя: {self.client_name}')

        dir_path = os.path.dirname(os.path.realpath(__file__))
        key_file = os.path.join(dir_path, 'client', f'{self.client_name}.key')
        if not os.path.exists(key_file):
            keys = RSA.generate(2048, os.urandom)
            with open(key_file, 'wb') as key:
                key.write(keys.export_key())
        else:
            with open(key_file, 'rb') as key:
                keys = RSA.import_key(key.read())

        db_path = os.path.join(dir_path, 'client', self.client_name)
        self.database = ClientDB(db_path)

        try:
            self.transport = ClientTransport(self.server_address,
                                             self.server_port,
                                             self.client_name,
                                             self.database,
                                             self.client_password,
                                             keys)
        except ServerError as error:
            message = QMessageBox()
            message.critical(None, 'Ошибка сервера', error.text)
            exit(1)
        self.transport.setDaemon(True)
        self.transport.start()

        del start_dialog

        main_window = ClientMainWindow(self.database, self.transport, keys)
        main_window.make_connection(self.transport)
        main_window.setWindowTitle(f'Чат Программа alpha release - {self.client_name}')
        self.client_app.exec_()

        self.transport.transport_shutdown()
        self.transport.join()

    @log
    def arg_parser(self):
        """Parsing command line arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_SERVER_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        parser.add_argument('-p', '--password', default='', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        self.server_address = namespace.addr
        self.server_port = namespace.port
        self.client_name = namespace.name
        self.client_password = namespace.password

        if not 1023 < self.server_port < 65536:
            logger.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {self.server_port}. '
                f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
            exit(1)


if __name__ == '__main__':
    client_1 = Client()
