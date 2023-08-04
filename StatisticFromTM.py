import sqlite3
from datetime import datetime

from utils import ApiTM
from pathlib import Path


def get_items_from_db(start_date, end_date):
    query = f'SELECT market_hash_name FROM hanuna WHERE \'{start_date} \' < buy_date < \'{end_date}\''
    items = cur.execute(query).fetchall()
    return items


def get_statistic_from_tm(start_date, end_date):
    """
    (market_hash_name, sell_price) - название и цена продажи
    Дата в виде 12-01-23
        """
    start_date = convert_to_timestamp(start_date)
    end_date = convert_to_timestamp(end_date)
    sell_history = acc.get_sell_history(start_date, end_date)

    sell_history_result = []
    for history_row in sell_history:
        if history_row["h_event"] != 'sell_go':
            continue
        item_name = history_row['market_hash_name']
        if history_row['stage'] == '2':
            price = round(int(history_row['paid']) / 100, 2)
        else:
            price = False
        sell_history_result.append((item_name, price))

    print(sell_history_result)
    return sell_history_result


def to_db(item):
    item_name = item[0]
    price = item[1] * 0.9
    if price < 100:
        price *= 10
    price = round(price, 2)

    query1 = f"""
    UPDATE hanuna
    SET sold_price = {price}
    WHERE market_hash_name = '{item_name}' 
      AND sold_price IS NULL
      AND ROWID = (
        SELECT ROWID
        FROM hanuna
        WHERE market_hash_name = '{item_name}' 
          AND sold_price IS NULL
        LIMIT 1
  );"""
    cur.execute(query1)
    con.commit()


def convert_to_timestamp(date_string):
    datetime_obj = datetime.strptime(date_string, '%d-%m-%y')
    timestamp = datetime_obj.timestamp()
    return int(timestamp)


def main():
    # buy_history = get_items_from_db(start_date_buy, end_date_buy)
    sell_history = get_statistic_from_tm(start_date_sell, end_date_sell)
    for item in sell_history:
        if not item:
            continue
        to_db(item)


if __name__ == '__main__':
    path_to_db = Path.cwd() / 'db' / 'PurchaseLogAndDuplicateCheckDB.db'
    con = sqlite3.connect(path_to_db)
    cur = con.cursor()
    api = '7GI98ntA4y99I7WMk26IlmkCJVWe6T9'
    acc = ApiTM.Account(api=api, currency='RUB')

    start_date_buy = '29-06-23'
    end_date_buy = '3-07-23'

    start_date_sell = '06-07-23'
    end_date_sell = '02-08-23'

    main()