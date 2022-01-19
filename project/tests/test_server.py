import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from project.server import process_client_message


class TestClassServer(unittest.TestCase):
    """Тестирование модуля server.py"""

    error_answer = {'response': 400,
                    'error': 'Bad request'}
    ok_answer = {'response': 200}

    def test_process_client_message(self):
        """Тест обработка корректного запроса от клиента"""
        self.assertEqual(process_client_message({
            'action': 'presence',
            'time': 111,
            'user': {'account_name': 'guest'}
            }), self.ok_answer)

    def test_process_client_message_without_action(self):
        """Тест обработка запроса от клиента без поля action"""
        self.assertEqual(process_client_message({
            'time': 111,
            'user': {'account_name': 'guest'}
            }), self.error_answer)

    def test_process_client_message_without_time(self):
        """Тест обработка запроса от клиента без поля time"""
        self.assertEqual(process_client_message({
            'action': 'presence',
            'user': {'account_name': 'guest'}
            }), self.error_answer)


    def test_process_client_message_without_user(self):
        """Тест обработка запроса от клиента без поля user"""
        self.assertEqual(process_client_message({
            'action': 'presence',
            'time': 111,
            }), self.error_answer)

    def test_process_client_message_with_wrong_action(self):
        """Тест обработка запроса от клиента c неверным action"""
        self.assertEqual(process_client_message({
            'action': 'msg',
            'time': 111,
            'user': {'account_name': 'user'}
            }), self.error_answer)


    def test_process_client_message_with_wrong_user(self):
        """Тест обработка запроса от клиента c неверным user"""
        self.assertEqual(process_client_message({
            'action': 'presence',
            'time': 111,
            'user': {'account_name': 'user'}
            }), self.error_answer)

if __name__ == '__main__':
    unittest.main()
