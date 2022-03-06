import sys
import json
import socket
import time
import argparse
import logging
import threading
import logs.config_client_log
from constants import *
from utils import *
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from logs.decos import log
from metaclasses import ClientValidator
from client_database import ClientDB

logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientValidator):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            FROM: self.account_name
        }

    def create_message(self):
        destination = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        with database_lock:
            if not self.database.check_user(destination):
                logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {destination}')
                return

        message_dict = {
            ACTION: MESSAGE,
            FROM: self.account_name,
            TO: destination,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name, destination, message)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.debug(f'Отправлено сообщение для пользователя {destination}')
            except OSError as err:
                if err.errno:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    logger.error('Не удалось передать сообщение. Таймаут соединения')

    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()

            elif command == 'help':
                self.print_help()

            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                        pass
                    logger.info('Завершение соединения.')
                time.sleep(0.5)
                break

            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    @staticmethod
    def print_help():
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_user=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_user=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')


class ClientReader(threading.Thread, metaclass=ClientValidator):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)

                except IncorrectDataRecivedError:
                    logger.error(f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and FROM in message and TO in message \
                            and MESSAGE_TEXT in message and message[TO] == self.account_name:
                        print(f'\n{message[FROM]}: {message[MESSAGE_TEXT]}')
                        with database_lock:
                            try:
                                self.database.save_message(message[FROM], self.account_name, message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                logger.error('Ошибка взаимодействия с базой данных')
                    elif ACTION in message and message[ACTION] == EXIT:
                        break
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')


@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def process_response_ans(message):
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_SERVER_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name


@log
def contacts_list_request(sock, name):
    logger.debug(f'Запрос контакт листа для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logger.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[ALERT]
    else:
        raise ServerError


@log
def add_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        CONTACT: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


@log
def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[ALERT]
    else:
        raise ServerError


@log
def remove_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: DEL_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


@log
def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


@log
def main():
    print('Консольный месседжер. Клиентский модуль.')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    logger.info(
        f'Запущен клиент с параметрами: адрес сервера: {server_address} , порт: {server_port}, '
        f'имя пользователя: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        transport.settimeout(1)

        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        logger.debug(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except ServerError as error:
        logger.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:

        database = ClientDB(client_name)
        database_load(transport, database, client_name)

        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Запущены процессы')

        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
