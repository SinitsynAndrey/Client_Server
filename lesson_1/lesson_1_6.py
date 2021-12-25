import chardet

FILE_NAME = 'test_file.txt'


def detect_file_encode(file):
    with open(file, 'rb') as f:
        content = f.read()
    encode_format = chardet.detect(content)
    content = content.decode(encode_format['encoding']).encode('utf-8')
    print(content.decode('utf-8'))


def create_file(file, lst):
    with open(file, 'w') as f:
        f.writelines(f'{line}\n' for line in lst)


create_file(FILE_NAME, ['сетевое программирование', 'сокет', 'декоратор'])
detect_file_encode(FILE_NAME)
