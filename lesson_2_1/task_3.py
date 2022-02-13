import platform
import subprocess
import ipaddress
import sys
from tabulate import tabulate


def create_ip_list(address, interval):
    ip_list = []
    initial_ip = ipaddress.ip_address(address)
    if int(str(initial_ip).split('.')[3]) + interval > 255:
        print('Неверно задан интервал ip адресов')
        sys.exit(1)
    for i in range(interval):
        ip_list.append(initial_ip + i)
    return ip_list


def host_range_ping_tab(address_list):
    address_dict = {'Reachable': [], 'Unreachable': []}
    for ip in address_list:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        response = subprocess.Popen(['ping', param, '1', str(ip)], stdout=subprocess.PIPE)
        if response.wait() == 0:
            address_dict['Reachable'].append(ip)
        else:
            address_dict['Unreachable'].append(ip)
    column = ['Reachable', 'Unreachable']
    print(tabulate(address_dict, headers=column))


if __name__ == '__main__':
    host_range_ping_tab(create_ip_list('81.19.86.1', 10))
