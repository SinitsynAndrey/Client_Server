import json


def write_order_to_json(item, quantity, price, buyer, date):
    dict_to_json = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date
    }

    with open('orders.json', 'r', encoding='utf-8') as f:
        orders_dict = json.load(f)
        orders_dict['orders'].append(dict_to_json)

    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders_dict, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    write_order_to_json(item='Продукт3%%', quantity=999, price=999, buyer='Олег', date='28.12.2021')
