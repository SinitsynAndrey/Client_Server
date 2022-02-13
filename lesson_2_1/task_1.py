import platform
import subprocess
import ipaddress


def create_ip_list(str_list):
    ip_list = []
    for ip in str_list:
        try:
            ip_list.append(ipaddress.ip_address(ip))
        except ValueError:
            ip_list.append(ip)
    return ip_list


def host_ping(address_list):
    for ip in address_list:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        response = subprocess.Popen(['ping', param, '1', str(ip)], stdout=subprocess.PIPE)
        if response.wait() == 0:
            print(f'{ip} - Узел доступен')
        else:
            print(f'{ip} - Узел недоступен')


if __name__ == '__main__':
    addresses = ['ya.ru', '123', '8.8.8.8', 'google.com', 'vk.com', '192.168.1.1', '10.10.10.10']
    host_ping(create_ip_list(addresses))
