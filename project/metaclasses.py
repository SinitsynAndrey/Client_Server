"""Metaclasses"""
import dis


class ServerValidator(type):
    """Server validating for correct socket initialization"""
    def __init__(cls, cls_name, bases, cls_dict):
        af_inet = False
        sock_stream = False
        for el in dis.Bytecode(cls_dict['create_socket']):
            if 'AF_INET' in el:
                af_inet = True
            if 'SOCK_STREAM' in el:
                sock_stream = True
        if not (af_inet and sock_stream):
            raise TypeError('Некорректная инициализация сокета.')

        for el in dis.Bytecode(cls_dict['main']):
            if 'connect' in el:
                raise TypeError('Использование метода connect недопустимо в серверном классе')

        super().__init__(cls_name, bases, cls_dict)


class ClientValidator(type):
    """Client validating for correct socket initialization"""
    def __init__(cls, cls_name, bases, cls_dict):
        af_inet = False
        sock_stream = False
        for el in dis.Bytecode(cls_dict['main']):
            if 'AF_INET' in el:
                af_inet = True
            if 'SOCK_STREAM' in el:
                sock_stream = True
            if ('accept' or 'listen') in el:
                print(el)
                raise TypeError('Использование метода accept и listen недопустимо в клиентском классе')
        if not (af_inet and sock_stream):
            raise TypeError('Некорректная инициализация сокета.')

        super().__init__(cls_name, bases, cls_dict)
