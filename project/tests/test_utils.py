import sys
import os
import json
import unittest
from socket import socket, AF_INET, SOCK_STREAM
from unittest.mock import patch
from project.constants import *

sys.path.append(os.path.join(os.getcwd(), '..'))
from project.utils import get_params, get_message, send_message


class TestClassUtils(unittest.TestCase):
    """Тестирвоание модуля utils.py"""

    def setUp(self):
        """Создание тестовых сокетов для тестирования функций отправки
        и получения сообщений"""

        # Создаем тестовый сокет для сервера
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', DEFAULT_PORT))
        self.server_socket.listen(REQUEST_NUMBER)

        # Создаем тестовый сокет для клиента
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((DEFAULT_SERVER_ADRESS, DEFAULT_PORT))

        self.client, self.client_address = self.server_socket.accept()

    def tearDown(self):
        """Закрываем созданные сокеты"""
        self.client.close()
        self.client_socket.close()
        self.server_socket.close()

    def test_get_message(self):
        """Тестирование корректного получения сообщения"""
        message = {'response': 200}
        test_message = json.dumps(message).encode(ENCODING)
        self.client_socket.send(test_message)
        response = get_message(self.client)
        self.assertEqual(message, response)

    def test_get_message_with_get_not_dict(self):
        """Тестирование функции get_message при отправке не словаря"""
        message = 'not dict'
        test_message = json.dumps(message).encode(ENCODING)
        self.client_socket.send(test_message)
        self.assertRaises(ValueError, get_message, self.client)

    def test_send_message_with_not_corrected_socket(self):
        """Тестирование функции send_message с некорректным сокетом"""
        self.client.close()
        message = 'test'
        self.assertRaises(OSError, send_message, self.client, message)

    @patch.object(sys, 'argv', ['utils.py', '-p', '8888', '-a', '127.0.0.1'])
    def test_get_params_with_all_params(self):
        """Тестирование функции get_params с корректно заданными
        параметрами адреса и порта"""
        self.assertEqual(get_params(), ('127.0.0.1', 8888))

    @patch.object(sys, 'argv', ['utils.py', '-p', '8888'])
    def test_get_params_with_port_in_params(self):
        """Тестирование функции get_params с корректно заданным
        портом и адресом по умолчанию"""
        self.assertEqual(get_params(), ('', 8888))

    @patch.object(sys, 'argv', ['utils.py', '-a', '127.0.0.1'])
    def test_get_params_with_address_in_params(self):
        """Тестирование функции get_params с корректно заданным
        адресом и портом по умолчанию"""
        self.assertEqual(get_params(), ('127.0.0.1', DEFAULT_PORT))

    def test_get_params_without_params(self):
        """Тестирование функции get_params с портом и адресом по умолчанию"""
        self.assertEqual(get_params(), ('', DEFAULT_PORT))

    @patch.object(sys, 'argv', ['utils.py', '-p', '66666'])
    def test_get_params_with_port_more_65535_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['utils.py', '-p', '1000'])
    def test_get_params_with_port_less_1024_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['utils.py', '-p'])
    def test_get_params_with_not_set_port_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['utils.py', '-a', '127001'])
    def test_get_params_with_incorrect_address_in_params(self):
        """Тестирование функции get_params с не корректно заданным адресом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['utils.py', '-a'])
    def test_get_params_with_not_set_address_in_params(self):
        """Тестирование функции get_params с не корректно заданным адресом"""
        self.assertRaises(SystemExit, get_params)


if __name__ == '__main__':
    unittest.main()
