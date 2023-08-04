import sqlite3
from pathlib import Path

from utils import Database, ApiTM


def price_on_sale():
    items = account.get_items_on_sale()
    price = 0
    for item in items:
        print(item["market_hash_name"])

        update_db(market_hash_name=item['market_hash_name'])
        price += item['price']
    print('price now', price)


def update_db(market_hash_name):
    """Обновляет столбец on_sale и ставит там True если предмет находится на продаже"""
    query1 = f"""
        UPDATE hanuna
        SET on_sale = {True}
        WHERE market_hash_name = '{market_hash_name}' 
          AND sold_price IS NULL
          AND on_sale IS NULL
          AND ROWID = (
            SELECT ROWID
            FROM hanuna
            WHERE market_hash_name = '{market_hash_name}' 
              AND sold_price IS NULL
              AND on_sale IS NULL
            LIMIT 1
      );"""
    print(query1)
    cur.execute(query1)
    con.commit()


def price_min():
    items = account.get_items_on_sale()
    price = 0
    print(f'Количество предметов: {len(items)}')
    for item in items:
        # print(item["market_hash_name"])
        price += current_prices.get_min_price(item["market_hash_name"])[0]/100
        # print(current_prices.get_min_price(item["market_hash_name"])[0]/100)
    print("price min", price)


if __name__ == "__main__":
    api = '7GI98ntA4y99I7WMk26IlmkCJVWe6T9'
    account = ApiTM.Account(api, 'RUB')
    # account.update_inventory()
    current_prices = Database.DatabaseTM()
    current_prices.full_update_db()

    path_to_db = Path.cwd() / 'db' / 'PurchaseLogAndDuplicateCheckDB.db'  # База данных статистики
    con = sqlite3.connect(path_to_db)
    cur = con.cursor()

    price_on_sale()
    price_min()
