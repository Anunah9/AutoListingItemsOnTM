# Бот получает список предметов доступных для продажи
# получает минимальную цену на маркете
# ищет в истории покупок и смотрит цену покупки
# считает цену по которой продать
# сравнивает с минимальной
# далее выбирает:
# если мин цена меньше желаемой то ставить желаемую
# иначе ставить минимальную.
import sqlite3

from utils import Database, ApiTM
from pathlib import Path


def get_min_price(db: Database.DatabaseTM, market_hash_name):
    try:
        return db.get_min_price(market_hash_name)[0] / 100
    except TypeError:
        print(market_hash_name)


def calculate_expected_sell_price(buy_price, commission_procent, expect_procent):
    procent = expect_procent / (0.9 * commission_procent)
    return buy_price * procent


def calculate_result_price(min_price_tm, expected_price):
    if expected_price < min_price_tm:
        return min_price_tm
    else:
        return expected_price


def buy_history_db(market_hash_name):
    """Возвращает список из предметов найденных в бд даже если предмет один"""
    path_to_db = Path.cwd() / 'db' / 'PurchaseLogAndDuplicateCheckDB.db'
    con = sqlite3.connect(path_to_db)
    cur = con.cursor()
    query = f'SELECT * FROM hanuna WHERE market_hash_name = "{market_hash_name}" AND on_sale IS NULL'
    items = cur.execute(query).fetchall()

    return items


def update_sell_state(item):
    path_to_db = Path.cwd() / 'db' / 'PurchaseLogAndDuplicateCheckDB.db'
    con = sqlite3.connect(path_to_db)
    cur = con.cursor()
    query = f'UPDATE hanuna SET on_sale = True WHERE market_hash_name = \'{item[0]}\' AND buy_date = \'{item[3]}\''
    cur.execute(query)
    con.commit()


def revoke_sell_state_all():
    path_to_db = Path.cwd() / 'db' / 'PurchaseLogAndDuplicateCheckDB.db'
    con = sqlite3.connect(path_to_db)
    cur = con.cursor()
    query = f'UPDATE hanuna SET on_sale = NULL'
    cur.execute(query)
    con.commit()


def inventory_handler(item):
    id_for_sell = item['id']
    market_hash_name = item['market_hash_name']
    min_price_on_tm = get_min_price(current_prices, market_hash_name)
    items_from_buy_history = buy_history_db(market_hash_name)
    try:
        buy_price = items_from_buy_history[0][2]
        print(buy_price)
    except IndexError:
        print('Вы не покупали этот предмет')
        return False
    expected_price = calculate_expected_sell_price(buy_price, commission_procent, expect_procent)
    result_price = calculate_result_price(min_price_on_tm, expected_price)
    print(f"""
    Минимальная цена: {min_price_on_tm}
    Ожидаемая цена: {expected_price}
    Итоговая цена: {result_price}
    Цена покупки: {buy_price}
    """)
    update_sell_state(items_from_buy_history[0])
    account.add_to_sale(id_for_sell, result_price * 100)



def main():
    for item in items_for_sell:
        if not inventory_handler(item):
            continue


if __name__ == '__main__':
    current_prices = Database.DatabaseTM()
    current_prices.full_update_db()

    api = '7GI98ntA4y99I7WMk26IlmkCJVWe6T9'
    account = ApiTM.Account(api, 'RUB')
    account.update_inventory()
    # account.remove_all_from_sale()
    items_for_sell = account.my_inventory()
    revoke_sell_state_all()

    commission_procent = 0.94 # В виде 0.95 = 5% потери при пополнении бафа
    expect_procent = 1.17  # В виде 1.2 = 20%
    main()
