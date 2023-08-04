import datetime
import numpy as np
from statistics import median
import pickle
import steampy.models
from steampy.client import SteamClient

class SteamMarketMethods:
    # Переменная для хранения экземпляра клиента SteamClient
    steamclient: steampy.client.SteamClient = None
    # Заголовки для HTTP запросов
    headers = {
        'Referer': 'https://steamcommunity.com/market/listings/730/',
        'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.2.807 Yowser/2.5 Safari/537.36'
    }

    def __init__(self):
        # Загружаем данные для авторизации при создании экземпляра класса
        self.load_login()
        # Если сессия не активна, выполняем авторизацию и сохраняем данные для последующих запусков
        if not self.steamclient.is_session_alive():
            self.write_login()

    def login_required(self):
        """Проверяет, требуется ли авторизация"""
        check = self.steamclient.is_session_alive()
        print('Is session alive: ', check)

    def load_login(self):
        """Загружает данные авторизации из файла 'logon.bin'"""
        with open('logon.bin', 'rb') as f:
            self.steamclient = pickle.load(f)

    def write_login(self):
        """Выполняет авторизацию через SteamClient и сохраняет данные в файл 'logon.bin'"""
        self.steamclient = SteamClient('97F914FB6333AC5416AF882DA9909A35')
        self.steamclient.login('sanek0904', 'Bazaranet101', './Anunah.txt')
        print(self.steamclient)
        with open('logon.bin', 'wb') as f:
            pickle.dump(self.steamclient, f)

    def get_steam_prices(self, item_name_id):
        """Получает цены на покупку и продажу для предмета с указанным идентификатором"""
        # Запрос отправляется на страницу с гистограммой цен для предмета
        url = 'https://steamcommunity.com/market/itemordershistogram?'
        params = {
            'country': 'RU',
            'language': 'english',
            'currency': 5,
            'item_nameid': int(item_name_id),
            'two_factor': 0
        }
        response = self.steamclient._session.get(url, params=params, headers=self.headers)
        print(response)
        response = response.json()
        first_buy_price, second_buy_price, first_sell_price, second_sell_price = None, None, None, None
        try:
            first_buy_price = response['buy_order_graph'][0][0]
        except IndexError:
            pass
        except KeyError:
            print(response)
        try:
            second_buy_price = response['buy_order_graph'][1][0]
        except IndexError:
            pass
        except KeyError:
            print(response)
        try:
            first_sell_price = response['sell_order_graph'][0][0]
        except IndexError:
            pass
        except KeyError:
            print(response)
        try:
            second_sell_price = response['sell_order_graph'][1][0]
        except IndexError:
            pass
        except KeyError:
            print(response)
        print(first_buy_price, second_buy_price, first_sell_price, second_sell_price)
        return first_buy_price, second_buy_price, first_sell_price, second_sell_price

    def get_price_history(self, market_hash_name):
        """Получает историю цен для предмета с указанным именем на торговой площадке Steam"""
        url = f'https://steamcommunity.com/market/pricehistory/'
        params = {'market_hash_name': market_hash_name,
                  'appid': '730',
                  'currency': '5',
                  'format': 'json'
                  }

        response = self.steamclient._session.get(url, params=params, headers=self.headers)
        print(response.url)
        print(f'Get Price History: {response}')

        if response.status_code != 200:
            return None
        try:
            status = response.json()['success']
        except TypeError:
            return None

        price_history = self.__convert_history(response.json()['prices'])
        return price_history


    def get_my_inventory(self):
        """Получает инвентарь пользователя на торговой площадке Steam для определенной игры (CS:GO)"""
        return self.steamclient.get_my_inventory(game=steampy.models.GameOptions.CS)

    def get_buy_history(self):
        """Получает историю покупок пользователя на торговой площадке Steam"""
        url = 'https://steamcommunity.com/market/myhistory'
        params = {
            'count': 100
        }
        response = self.steamclient._session.get(url, headers=self.headers, params=params)
        print(f'Get Buy History: {response}')

        if response.status_code != 200:
            return None
        try:
            status = response.json()['success']

        except TypeError:
            return None
        return response.json()

    def __convert_history(self, price_history):
        """Преобразует историю цен, полученную в формате JSON, в удобный формат списка"""
        for date in price_history:
            date[0] = date[0].split(' ')
            date[0] = date[0][:3]
            date[0] = ' '.join(date[0])
            date[0] = datetime.datetime.strptime(date[0], "%b %d %Y")
            date[1] = float(date[1])
            date[2] = int(date[2])
        return price_history

    def find_anomalies(self, price_history):
        """Ищет аномалии в истории цен и отделяет их от основных данных"""
        price_history_prices = list(map(lambda price: price[1], price_history))
        price_history_without_anomalies = []
        anomalies = []
        random_data_std = np.std(price_history_prices)
        random_data_mean = np.mean(price_history_prices)
        anomaly_cut_off = random_data_std * 3

        lower_limit = random_data_mean - anomaly_cut_off
        upper_limit = random_data_mean + anomaly_cut_off

        for indx, outlier in enumerate(price_history_prices):
            if outlier < upper_limit or outlier > lower_limit:
                price_history_without_anomalies.append(outlier)
            else:
                anomalies.append(outlier)
        print('Аномалии', anomalies)
        return price_history

    @staticmethod
    def get_sales_for_days(price_history, days):
        """Возвращает историю продаж за указанное количество дней"""
        sales = []
        now = datetime.datetime.now()
        delta = datetime.timedelta(days)
        days_date = now - delta
        for date in price_history:
            if date[0] > days_date:
                sales.append(date)
        return sales

    @staticmethod
    def peak_history(price_history):
        """Возвращает список продаж, у которых цена выше медианной цены"""
        try:
            median_price = median(list(map(lambda x: x[1], price_history)))
        except:
            return []
        peaks = []
        for date in price_history:
            if date[1] > median_price:
                peaks.append(date)
        return peaks

    @staticmethod
    def get_avg_price(price_history_peaks):
        """Рассчитывает среднюю цену на основе списка продаж"""
        count_for_middle_price = 0
        cumm_price = 0
        for date in price_history_peaks:
            count_for_middle_price += date[2]
            cumm_price += date[1] * date[2]
        try:
            middle_price = cumm_price / count_for_middle_price
        except ZeroDivisionError:
            middle_price = 0
        return middle_price

    @staticmethod
    def get_count_sales(price_history):
        """Возвращает общее количество продаж из истории цен"""
        count = 0
        for sell in price_history:
            count += sell[2]
        return count

    def get_clear_price_history(self, price_history_days):
        """Удаляет аномалии и возвращает чистую историю цен за указанный период"""
        sell_prices = self.peak_history(price_history_days)
        sell_prices_without_anomalies = self.find_anomalies(sell_prices)
        return sell_prices_without_anomalies

    def create_buy_order(self, market_hash_name, price, quantity):
        """Создает ордер на покупку предмета на торговой площадке Steam"""
        url = 'https://steamcommunity.com/market/createbuyorder/'
        params = {
            'sessionid': self.steamclient._session.cookies.values()[0],
            'currency': 5,
            'appid': 730,
            'market_hash_name': market_hash_name,
            'price_total': price * 100,
            'quantity': quantity,
            'billing_state': '',
            'save_my_address': 0
        }
        print(params)

        response = self.steamclient._session.post(url, params, headers=self.headers)
        print(response.json())

    def get_balance(self, cookie):
        """Получает баланс пользователя на торговой площадке Steam"""
        url = 'https://steamcommunity.com/market/'
        response = self.steamclient._session.get(url, cookies=cookie)
        print(response.json())



