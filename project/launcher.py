"""Запускает сервер и  4 клиента (2 на чтение и 2 на отправку)"""
from subprocess import Popen, CREATE_NEW_CONSOLE

Popen('python server.py', creationflags=CREATE_NEW_CONSOLE)

for i in range(4):
    Popen(f'python client.py -n test_{i}', creationflags=CREATE_NEW_CONSOLE)




