def convert_to_byte(lst):
    for item in lst:
        byte_item = item.encode('utf-8')
        print(byte_item, type(byte_item))
        str_item = byte_item.decode('utf-8')
        print(str_item, type(str_item))


convert_to_byte(['разработка', 'администрирование', 'protocol', 'standard'])
