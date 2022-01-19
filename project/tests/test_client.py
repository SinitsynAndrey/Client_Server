import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from project.client import preparation_message, processing_answer


class TestClassClient(unittest.TestCase):
    """Тестирование модуля client.py"""

    def test_preparation_message(self):
        """Тест корректной подготовки сообщения"""
        test = preparation_message()
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
        test = preparation_message('user')
        test['time'] = 111
        self.assertNotEqual(test, {
            'action': 'presence',
            'time': 111,
            'user': {
                'account_name': 'guest'
            }
        })

    def test_processing_answer_200(self):
        """ Тест корректной обработки ответа с кодом 200"""
        self.assertEqual(processing_answer({'response': 200}),
                         'Соединение установлено')

    def test_processing_answer_400(self):
        """ Тест корректной обработки ответа с кодом 400"""
        self.assertEqual(processing_answer({'response': 400, 'error': 'Bad request'}),
                         'Connection error')


if __name__ == '__main__':
    unittest.main()
