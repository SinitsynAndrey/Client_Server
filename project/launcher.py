"""Запускает сервер и  4 клиента (2 на чтение и 2 на отправку)"""
from subprocess import Popen, CREATE_NEW_CONSOLE

Popen('python server.py', creationflags=CREATE_NEW_CONSOLE)

for _ in range(2):
    Popen('python client.py -m send', creationflags=CREATE_NEW_CONSOLE)
    Popen('python client.py -m listen', creationflags=CREATE_NEW_CONSOLE)



