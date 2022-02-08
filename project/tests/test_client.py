"""Unit testing client.py"""
import sys
import os
import unittest
from unittest.mock import patch
from project.constants import *

sys.path.append(os.path.join(os.getcwd(), '..'))
from project.client import preparation_presence_message, processing_answer, get_params


class TestClassClient(unittest.TestCase):
    """Class testing client.py"""

    def test_preparation_message(self):
        """Тест корректной подготовки сообщения"""
        test = preparation_presence_message("test")
        test['time'] = 111
        self.assertEqual(test, {
            'action': 'presence',
            'time': 111,
            'user': {
                'account_name': 'test'
            }
        })

    def test_wrong_preparation_message(self):
        """Тест ошибки при передачи в сообщение account_name"""
        test = preparation_presence_message('user')
        test['time'] = 111
        self.assertNotEqual(test, {
            ACTION: PRESENCE,
            TIME: 111,
            USER: {
                ACCOUNT_NAME: 'guest'
            }
        })

    def test_processing_answer_200(self):
        """ Тест корректной обработки ответа с кодом 200"""
        with self.assertLogs() as captured:
            processing_answer({RESPONSE: 200, ALERT: 'dscs'})
        self.assertEqual(captured.records[0].getMessage(),
                         "Получен ответ от сервера: {'response': 200, 'alert': 'dscs'}")

    def test_processing_answer_400(self):
        """ Тест
         обработки ответа с кодом 400"""
        self.assertRaises(SystemExit, processing_answer, {RESPONSE: 400,
                                                          ERROR: 'dfe'})

    def test_processing_without_response(self):
        """ Тест корректной обработки ответа с кодом 400"""
        self.assertRaises(SystemExit, processing_answer, {'answer', 400})

    def test_processing_incorrect_type(self):
        """ Тест корректной обработки ответа с кодом 400"""
        self.assertRaises(TypeError, processing_answer, [RESPONSE, 400])

    @patch.object(sys, 'argv', ['client.py', '-p', '8888', '-a', '127.0.0.1'])
    def test_get_params_with_all_params(self):
        """Тестирование функции get_params с корректно заданными
        параметрами адреса, порта и мода"""
        self.assertEqual(get_params(), ('127.0.0.1', 8888, None))

    @patch.object(sys, 'argv', ['client.py', '-p', '8888'])
    def test_get_params_with_port_in_params(self):
        """Тестирование функции get_params.
         с корректно заданным
        портом и модом и адресом по умолчанию"""
        self.assertEqual(get_params(), ('127.0.0.1', 8888, None))

    @patch.object(sys, 'argv', ['client.py', '-a', '127.0.0.1'])
    def test_get_params_with_address_in_params(self):
        """Тестирование функции get_params с корректно заданным
        адресом и портом по умолчанию"""
        self.assertEqual(get_params(), ('127.0.0.1', 7777, None))

    @patch.object(sys, 'argv', ['client.py', '-p', '66666'])
    def test_get_params_with_port_more_65535_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['client.py', '-p', '1000'])
    def test_get_params_with_port_less_1024_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['client.py', '-p'])
    def test_get_params_with_not_set_port_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(AttributeError, get_params)

    @patch.object(sys, 'argv', ['client.py', '-a', '127001'])
    def test_get_params_with_incorrect_address_in_params(self):
        """Тестирование функции get_params с не корректно заданным адресом"""
        self.assertRaises(SystemExit, get_params)


if __name__ == '__main__':
    unittest.main()
