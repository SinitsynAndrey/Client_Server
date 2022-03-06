import sys
import os
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.getcwd(), '..'))
from project.server import get_params


class TestClassServer(unittest.TestCase):
    """Тестирование модуля server.py"""

    @patch.object(sys, 'argv', ['server.py', '-p', '8888', '-a', '127.0.0.1'])
    def test_get_params_with_all_params(self):
        """Тестирование функции get_params с корректно заданными
        параметрами адреса, порта и мода"""
        self.assertEqual(get_params(), ('127.0.0.1', 8888))

    @patch.object(sys, 'argv', ['server.py', '-p', '8888'])
    def test_get_params_with_port_in_params(self):
        """Тестирование функции get_params.
         с корректно заданным
        портом и модом и адресом по умолчанию"""
        self.assertEqual(get_params(), ('', 8888))

    @patch.object(sys, 'argv', ['server.py', '-a', '127.0.0.1'])
    def test_get_params_with_address_in_params(self):
        """Тестирование функции get_params с корректно заданным
        адресом и портом по умолчанию"""
        self.assertEqual(get_params(), ('127.0.0.1', 7777))

    @patch.object(sys, 'argv', ['client_old.py', '-p', '66666'])
    def test_get_params_with_port_more_65535_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['client_old.py', '-p', '1000'])
    def test_get_params_with_port_less_1024_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['client_old.py', '-p'])
    def test_get_params_with_not_set_port_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(AttributeError, get_params)

    @patch.object(sys, 'argv', ['client_old.py', '-a', '127001'])
    def test_get_params_with_incorrect_address_in_params(self):
        """Тестирование функции get_params с не корректно заданным адресом"""
        self.assertRaises(SystemExit, get_params)


if __name__ == '__main__':
    unittest.main()
