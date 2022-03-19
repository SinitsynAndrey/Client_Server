"""Запускает сервер и  4 клиента (2 на чтение и 2 на отправку)"""
from subprocess import Popen, CREATE_NEW_CONSOLE

Popen('python server.py')

for i in range(2):
    Popen(f'python client.py', creationflags=CREATE_NEW_CONSOLE)
