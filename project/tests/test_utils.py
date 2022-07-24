import sys
import os
import json
import unittest
from socket import socket, AF_INET, SOCK_STREAM
from project.constants import *
sys.path.append(os.path.join(os.getcwd(), '..'))
from project.utils import get_message, send_message


class TestClassUtils(unittest.TestCase):
    """Тестирвоание модуля utils.py"""

    def setUp(self):
        """Создание тестовых сокетов для тестирования функций отправки
        и получения сообщений"""

        # Создаем тестовый сокет для сервера
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(('', int(DEFAULT_PORT)))
        self.server_socket.listen(REQUEST_NUMBER)

        # Создаем тестовый сокет для клиента
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((DEFAULT_SERVER_ADDRESS, int(DEFAULT_PORT)))

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


if __name__ == '__main__':
    unittest.main()
