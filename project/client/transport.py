import socket
import time
import threading
import hashlib
import hmac
import binascii
from utils import *
from errors import ServerError
from logs.decos import log
from PyQt5.QtCore import pyqtSignal, QObject

logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):

    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, server_address, server_port, account_name, database, password, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.server_address = server_address
        self.server_port = server_port
        self.account_name = account_name
        self.password = password
        self.keys = keys
        self.database = database
        self.transport = None

        self.connection_init()
        try:
            self.user_list_request()
            self.contacts_list_request()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
        self.running = True

    def connection_init(self):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((self.server_address, self.server_port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Установлено соединение с сервером')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.account_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        logger.debug(f'Passwd hash ready: {passwd_hash_string}')

        pubkey = self.keys.publickey().export_key().decode('ascii')

        try:
            with sock_lock:
                send_message(self.transport, self.create_presence(pubkey))
                ans = get_message(self.transport)
                logger.debug(f'Server response = {ans}.')
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        ans_data = ans[ALERT]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = {RESPONSE: 511,
                                  ALERT: binascii.b2a_base64(digest).decode('ascii')}
                        send_message(self.transport, my_ans)
                        self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError) as err:
            logger.debug(f'Connection error.', exc_info=err)
            raise ServerError('Сбой соединения в процессе авторизации.')

        logger.info('Соединение с сервером успешно установлено.')

    def user_list_request(self):
        logger.debug(f'Запрос списка известных пользователей {self.account_name}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }
        with sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[ALERT])
        else:
            raise ServerError

    def contacts_list_request(self):
        logger.debug(f'Запрос контакт листа для пользователя {self.account_name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.account_name
        }
        logger.debug(f'Сформирован запрос {req}')
        send_message(self.transport, req)
        ans = get_message(self.transport)
        logger.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for el in ans[ALERT]:
                self.database.add_contact(el)
        else:
            raise ServerError

    def create_presence(self, pubkey):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.account_name,
                PUBLIC_KEY: pubkey
            }
        }
        logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.account_name}')
        return out

    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }
        with sock_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            FROM: self.account_name,
            TO: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        with sock_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def key_request(self, user):
        logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user
        }
        with sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 511:
            return ans[ALERT]
        else:
            logger.error(f'Не удалось получить ключ собеседника{user}.')

    def process_server_ans(self, message):
        logger.debug(f'Разбор сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and FROM in message \
                and TO in message \
                and MESSAGE_TEXT in message \
                and message[TO] == self.account_name:
            logger.debug(f'Получено сообщение от пользователя {message[FROM]}:'
                         f'{message[MESSAGE_TEXT]}')
            self.new_message.emit(message)

    def run(self):
        logger.debug('Запущен процесс - приёмник сообщений с сервера.')
        while self.running:
            time.sleep(1)
            with sock_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)

    def add_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.account_name,
            CONTACT: contact
        }
        send_message(self.transport, req)
        ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка создания контакта')

    def remove_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: DEL_CONTACT,
            TIME: time.time(),
            USER: self.account_name,
            CONTACT: contact
        }
        send_message(self.transport, req)
        ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка удаления клиента')
