import sys
import argparse
import logging

from PyQt5.QtWidgets import QApplication

from constants import *
from errors import ServerError
from logs.decos import log
from client.client_database import ClientDB
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from client.main_window import ClientMainWindow

logger = logging.getLogger('client')


class Client:
    def __init__(self):
        self.server_address = None
        self.server_port = None
        self.client_name = None

        self.arg_parser()

        self.client_app = QApplication(sys.argv)

        if not self.client_name:
            start_dialog = UserNameDialog()
            self.client_app.exec_()
            if start_dialog.ok_pressed:
                self.client_name = start_dialog.client_name.text()
                del start_dialog
            else:
                sys.exit(0)

        logger.debug(
            f'Запущен клиент с парамертами: адрес сервера: {self.server_address} , '
            f'порт: {self.server_port}, имя пользователя: {self.client_name}')

        self.database = ClientDB(self.client_name)

        try:
            self.transport = ClientTransport(self.server_address,
                                             self.server_port,
                                             self.client_name,
                                             self.database)
        except ServerError as error:
            print(error.text)
            sys.exit(1)
        self.transport.setDaemon(True)
        self.transport.start()

        main_window = ClientMainWindow(self.database, self.transport)
        main_window.make_connection(self.transport)
        main_window.setWindowTitle(f'Чат Программа alpha release - '
                                   f'{self.client_name}')
        self.client_app.exec_()

        self.transport.transport_shutdown()
        self.transport.join()

    @log
    def arg_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_SERVER_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        self.server_address = namespace.addr
        self.server_port = namespace.port
        self.client_name = namespace.name

        if not 1023 < self.server_port < 65536:
            logger.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {self.server_port}. '
                f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
            exit(1)


if __name__ == '__main__':
    client_1 = Client()
