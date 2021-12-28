from chardet import detect
import re
import csv


def get_data(file_lst):
    DATA_FILE_NAME = 'main_data.csv'

    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы'],
                 os_prod_list,
                 os_name_list,
                 os_code_list,
                 os_type_list]

    for file in file_lst:
        with open(file, 'rb') as f:
            content = f.read()
            encode_format = detect(content)
            content = content.decode(encode_format['encoding']).encode('utf-8').decode('utf-8')
        os_prod_list.append(re.findall(r'Изготовитель системы:\s*(.+)\b', content)[0])
        os_name_list.append(re.findall(r'Название ОС:\s*(.+)\r', content)[0])
        os_code_list.append(re.findall(r'Код продукта:\s*(.+)\r', content)[0])
        os_type_list.append(re.findall(r'Тип системы:\s*(.+)\r', content)[0])
    with open('main_data.csv', 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerows(main_data)

    return DATA_FILE_NAME


def write_to_csv(csv_file):
    main_data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        main_data.append(next(csv_reader))
        for el in next(csv_reader):
            main_data.append([el])
        for row in csv_reader:
            for i, el in enumerate(row):
                main_data[i+1].append(el)
    print(main_data)

    with open('exercise_1_result.csv', 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerows(main_data)


if __name__ == '__main__':

    FILES = ['info_1.txt', 'info_2.txt', 'info_3.txt']
    write_to_csv(get_data(FILES))

"""
Понимаю что сделал непойми что) Просто не до конца понял задание. Если мы в функцию write_to_csv передаем 
ссылку на csv файл, то какие данные нужно получить вызовом функции get_data. Согласно заданию выше все
данные в фукции get_data мы уже записали в файл (в неверном формате). Чтобы выполнить условие задачи 
(насколько я его понял), get_data у меня просто название csv файла.
Можно было бы в get_data в списке main_data собрать всё в нужном формате и передать этот список в write_to_csv, 
но я так понимаю это перечило бы заданию.

"""