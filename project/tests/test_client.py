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
        test = preparation_presence_message()
        test['time'] = 111
        self.assertEqual(test, {
            'action': 'presence',
            'time': 111,
            'user': {
                'account_name': 'guest'
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
            processing_answer({RESPONSE: 200})
        self.assertEqual(captured.records[0].getMessage(),
                         'Соединение с сервером установлено.')

    def test_processing_answer_400(self):
        """ Тест
         обработки ответа с кодом 400"""
        self.assertRaises(SystemExit, processing_answer, {RESPONSE: 400})

    def test_processing_without_response(self):
        """ Тест корректной обработки ответа с кодом 400"""
        self.assertRaises(SystemExit, processing_answer, {'answer', 400})

    def test_processing_incorrect_type(self):
        """ Тест корректной обработки ответа с кодом 400"""
        self.assertRaises(TypeError, processing_answer, [RESPONSE, 400])

    @patch.object(sys, 'argv', ['client.py', '-p', '8888', '-a', '127.0.0.1', '-m', 'listen'])
    def test_get_params_with_all_params(self):
        """Тестирование функции get_params с корректно заданными
        параметрами адреса, порта и мода"""
        self.assertEqual(get_params(), ('127.0.0.1', 8888, 'listen'))

    @patch.object(sys, 'argv', ['client.py', '-p', '8888', '-m', 'listen'])
    def test_get_params_with_port_in_params(self):
        """Тестирование функции get_params.
         с корректно заданным
        портом и модом и адресом по умолчанию"""
        self.assertEqual(get_params(), ('127.0.0.1', 8888, 'listen'))

    @patch.object(sys, 'argv', ['client.py', '-a', '127.0.0.1', '-m', 'listen'])
    def test_get_params_with_address_in_params(self):
        """Тестирование функции get_params с корректно заданным
        адресом и портом по умолчанию"""
        self.assertEqual(get_params(), ('127.0.0.1', 7777, 'listen'))

    @patch.object(sys, 'argv', ['client.py', '-p', '66666', '-m', 'listen'])
    def test_get_params_with_port_more_65535_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['client.py', '-p', '1000', '-m', 'listen'])
    def test_get_params_with_port_less_1024_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(SystemExit, get_params)

    @patch.object(sys, 'argv', ['client.py', '-p', '-m', 'listen'])
    def test_get_params_with_not_set_port_in_params(self):
        """Тестирование функции get_params с не корректно заданным портом"""
        self.assertRaises(AttributeError, get_params)

    @patch.object(sys, 'argv', ['client.py', '-a', '127001', '-m', 'listen'])
    def test_get_params_with_incorrect_address_in_params(self):
        """Тестирование функции get_params с не корректно заданным адресом"""
        self.assertRaises(SystemExit, get_params)


if __name__ == '__main__':
    unittest.main()
