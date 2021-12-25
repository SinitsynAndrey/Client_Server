def convert_to_byte(lst):
    bytes_lst = list(map(lambda x: eval(f"b'{x}'"), lst))
    for item in bytes_lst:
        print(type(item), item, len(item))


convert_to_byte(['class', 'function', 'method'])
