"""Сервер."""

import logging
import argparse
import os
import re
import sys
import configparser
from server.server_database import ServerDB
from server.core import Server
from server.main_window import MainWindow

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

logger = logging.getLogger('server')


def get_params():
    """Get parameters from ini file and from command line."""
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server/server.ini'}")

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', nargs='?')
    parser.add_argument('-a', type=str, nargs='?')
    args = parser.parse_args()

    if args.a:
        if not re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', args.a):
            logger.error('Неверно задан адрес')
            sys.exit(1)
        config['SETTINGS']['listen_address'] = args.a
    if args.p:
        config['SETTINGS']['port'] = args.p

    return config


def run_server():
    """Start server application."""
    config = get_params()

    db_path = os.path.join(config['SETTINGS']['Database_path'],
                           config['SETTINGS']['Database_file'])

    database = ServerDB(db_path)

    server = Server(config['SETTINGS']['listen_address'],
                    int(config['SETTINGS']['port']),
                    database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(database, server, config)

    server_app.exec_()


if __name__ == '__main__':
    logger.info('Запуск сервера')
    run_server()
