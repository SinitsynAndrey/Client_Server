def convert_to_byte(lst):
    for item in lst:
        try:
            item_byte = eval(f'b"{item}"')
            print(f'"{item}" в байтовом типе: {item_byte}')
        except SyntaxError:
            print(f'"{item}" невозможно записать в байтовом типе')


convert_to_byte(['attribute', 'класс', 'функция', 'type'])
