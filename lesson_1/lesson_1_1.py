def check_type(ls):
    for item in ls:
        print(f'{item} - {type(item)}')


check_type(['разработка', 'сокет', 'декоратор'])
check_type(['\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
            '\u0441\u043e\u043a\u0435\u0442',
            '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'])
