from datetime import datetime
import pprint
from http.cookies import SimpleCookie

import pandas
import requests
from bs4 import BeautifulSoup
from pycbrf.toolbox import ExchangeRates
import sqlite3


def to_db(_data):
    con = sqlite3.connect('db/PurchaseLogAndDuplicateCheckDB.db')
    cur = con.cursor()
    query = f"""INSERT INTO hanuna (market_hash_name, price_CNY, price_RUB, buy_date) VALUES (?, ?, ?, ?)"""
    cur.executemany(query, _data)
    con.commit()


def get_statistic(_page):
    url = f'https://buff.163.com/market/buy_order/history?game=csgo&page_num={_page}'
    response = requests.get(url, cookies=BUFF_COOKIE)
    soup = BeautifulSoup(response.text, 'lxml')
    orders = soup.find('tbody', class_='list_tb_csgo')
    order = orders.find_all('tr')
    return order


def timestamp_to_date(timestamp):
    try:
        # Преобразование timestamp в объект datetime
        dt_object = datetime.fromtimestamp(timestamp)
        # Форматирование даты в нужный вид
        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def convert_price(_price, _date):
    # exchange_rate = float(ExchangeRates(_date)['CNY'].value)
    exchange_rate = 12.64
    price = _price * exchange_rate
    return price


def convert_date(_date):
    date = datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
    return date


def sort_order(_order):
    list_items = []
    for order in _order:
        print(order)
        name = order.find('span', class_='textOne').text
        price_cny = float(order.find('strong', class_='f_Strong').text.split(' ')[1])
        date_timestamp = int(order.find('span', class_='moment-ts')['data-ts'])
        buy_date = timestamp_to_date(date_timestamp)
        price_rub = round(convert_price(price_cny, buy_date), 2)
        try:
            order.find('p', class_='c_Green').text.replace(' ', '')
        except AttributeError:
            continue
        list_items.append((name, price_cny, price_rub, buy_date))
    return list_items


def to_excel(_data):
    frame = pandas.DataFrame(_data)
    frame.to_excel('statistic.xlsx')


def main():
    sorted_orders = []
    for i in range(1, 13):
        print(f'page {i}')
        orders = get_statistic(i)
        sorted_orders += sort_order(orders)
        to_db(sorted_orders)


if __name__ == '__main__':
    raw_cookie = 'Device-Id=uC6VJw0tNQ3gdizU4kz1; P_INFO=7-9272445287|1683632250|1|netease_buff|00&99|null&null&null#RU&null#10#0|&0||7-9272445287; Locale-Supported=ru; game=csgo; session=1-Lnomd2PiiJ3nV41wAmCc5joxBWZgZYPzx3v16owhRg5K2037019629; csrf_token=ImRmYjNmZjM0ZjI3MTRmYmQxMWVlZWI5ZDE0ZjFiOGI5Y2RjYTdhNmYi.F6uUxA.rV6jh0AQan_VUIc0I7AvoniRrOg'
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    BUFF_COOKIE = {k: v.value for k, v in cookie.items()}
    main()
