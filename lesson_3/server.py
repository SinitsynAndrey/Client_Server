import socket
import json
from constants import *
from utils import get_message, send_message, get_params


def process_client_message(message):
    if 'action' in message and message['action'] == 'presence' \
            and 'time' in message \
            and 'user' in message and message['user']['account_name'] == 'guest':
        return {'response': 200}
    else:
        return {'response': 400,
                'error': 'Bad request'}


def main():
    client_adress, client_port = get_params()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((client_adress, client_port))
    transport.listen(REQUEST_NUMBER)

    while True:
        client, addr = transport.accept()
        try:
            message_from_client = get_message(client)
        except (ValueError, json.decoder.JSONDecodeError):
            print('Получено неверное сообщение от пользователя')
            send_message(client, {'response': 400,
                                  'error': 'Bad request'})
            continue
        msg = process_client_message(message_from_client)
        send_message(client, msg)
        client.close()


if __name__ == '__main__':
    main()
