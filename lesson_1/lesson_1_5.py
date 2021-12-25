import subprocess
import chardet
import platform


def subproc(resource):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping', param, '4', resource]
    ping = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in ping.stdout:
        encode_format = chardet.detect(line)
        result = line.decode(encode_format['encoding']).encode('utf-8')
        print(result.decode('utf-8'))


subproc('yandex.ru')
subproc('youtube.com')
