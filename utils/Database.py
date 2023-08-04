import os
import sqlite3
import wget
import requests
import pandas as pd
from pathlib import Path


def item_data(func):
    def get_item_statistic(*args):
        self, item_name = args
        query = f"SELECT * FROM test WHERE name = '{item_name}'"
        self.data = self.con.execute(query).fetchall()
        func(*args)
    return get_item_statistic


class Database(object):
    def __init__(self, db_name, name_table):
        self.data = None
        self.con = sqlite3.connect(db_name)
        self.name_table = name_table
        self.item_name = None

    @item_data
    def price_history(self, item_name):
        """Список цен предмета"""
        prices = []
        for item in self.data:
            prices.append(item[2])
        print(prices)
        return prices

    @item_data
    def price_with_date(self, item_name):
        """Список цен и дат предмета"""
        price_with_date = []
        for item in self.data:
            price_with_date.append((item[2], item[1]))
        return price_with_date


class DatabaseTM:
    def __init__(self):
        self.name_table = 'test'
        self.__db_name = self.__get_name_db_csgo_tm()
        self.path_to_current_prices_db = Path.cwd() / 'db' / 'current_prices_db_tm.db'
        self.path_to_temp_db = Path.cwd() / 'db' / f'{self.__db_name}'
        self.con = sqlite3.connect(self.path_to_current_prices_db, check_same_thread=False)
        self.cur = self.con.cursor()

    @staticmethod
    def __get_name_db_csgo_tm():
        url = 'https://market.csgo.com/itemdb/current_730.json'
        response = requests.get(url).text.split('"')
        __db_name = response[5]
        return __db_name

    def __get_db_from_csgo_tm(self):
        url = f'https://market.csgo.com/itemdb/{self.__db_name}'
        wget.download(url, '.\db')

    def __csv_converter(self):
        data = pd.read_csv(self.path_to_temp_db, index_col=False, sep=";"
                           )
        df = pd.DataFrame(data)
        df.head()
        df.pop('c_base_id')
        df.pop('c_rarity')
        df.pop('c_name_color')
        df.pop('c_stickers')
        df.pop('c_slot')
        df.pop('c_offers')
        df.pop('c_price_updated')
        df.pop('c_quality')
        df.pop('c_heroid')
        df.pop('c_pop')
        self.__to_database(df)

    def __to_database(self, df):
        try:
            self.cur.execute("""drop table test""")
            df.to_sql('test', self.con)
        except sqlite3.OperationalError:
            df.to_sql('test', self.con)

    def full_update_db(self):
        """На сайте БД обновляется раз в минуту, примерно на 15 секунде минуты"""
        self.__get_db_from_csgo_tm()
        self.__csv_converter()
        os.remove(self.path_to_temp_db)
        print('Готово')

    def get_prices(self, market_hash_name):
        """Возвращает список кортежей типа (price, classid)"""
        query = f'SELECT c_price, c_classid FROM test WHERE c_market_hash_name = "{market_hash_name}"'
        data = self.cur.execute(query)
        data = data.fetchall()
        return data

    def get_min_price(self, market_hash_name):
        """Возвращает кортеж (price, classid) предмета с минимальной ценой"""
        query = f'SELECT c_price, c_classid FROM test WHERE c_market_hash_name = "{market_hash_name}" GROUP BY ' \
                f'c_price'
        min_price = self.cur.execute(query)
        min_price = min_price.fetchone()
        return min_price
