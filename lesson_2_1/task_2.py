import platform
import subprocess
import ipaddress
import sys


def create_ip_list(address, interval):
    ip_list = []
    initial_ip = ipaddress.ip_address(address)
    if int(str(initial_ip).split('.')[3]) + interval > 255:
        print('Неверно задан интервал ip адресов')
        sys.exit(1)
    for i in range(interval):
        ip_list.append(initial_ip + i)
    return ip_list


def host_range_ping(address_list):
    for ip in address_list:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        response = subprocess.Popen(['ping', param, '1', str(ip)], stdout=subprocess.PIPE)
        if response.wait() == 0:
            print(f'{ip} - Узел доступен')
        else:
            print(f'{ip} - Узел недоступен')


if __name__ == '__main__':
    host_range_ping(create_ip_list('81.19.86.1', 10))

