"""Запускает сервер и  2 клиента"""
from subprocess import Popen, CREATE_NEW_CONSOLE

if __name__ == "__main__":
    Popen('python server.py')

    for i in range(2):
        Popen(f'python client_run.py -n test_{i} -p 123', creationflags=CREATE_NEW_CONSOLE)
