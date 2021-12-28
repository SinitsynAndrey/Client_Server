import yaml


def write_to_yaml(yaml_lst, yaml_int, yaml_dict):
    yaml_dict = {
        'yaml_lst': yaml_lst,
        'yaml_int': yaml_int,
        'yaml_dict': yaml_dict
    }

    with open('file.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(yaml_dict, f, default_flow_style=False, allow_unicode=True)

    with open('file.yaml', encoding='utf-8') as f:
        from_yaml_date = yaml.load(f, Loader=yaml.FullLoader)

    print('Записанные и загруженные данные совпадают' if yaml_dict == from_yaml_date else 'Что-то пошло не так')


if __name__ == '__main__':

    lst_to_write = ['А', 'Б', 'В', 'Г']
    int_to_write = 10
    dict_to_write = {
        1: '$1',
        2: '©2',
        3: '£3'
    }

    write_to_yaml(yaml_lst=lst_to_write, yaml_int=int_to_write, yaml_dict=dict_to_write)
