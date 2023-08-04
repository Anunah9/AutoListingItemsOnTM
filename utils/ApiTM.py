import datetime
import json

import requests
import websocket


def convert_date(date_time):
    _format = ' %b %d, %Y (%I:%M:%S) %Z'  # Формат

    datetime_str = datetime.datetime.strptime(date_time, _format)
    print(datetime_str)
    return datetime_str


def convert_exterior(exterior):
    if exterior == 'Factory New':
        exterior = 'FN'
    if exterior == 'Minimal Wear':
        exterior = 'MW'
    if exterior == 'Field-Tested':
        exterior = 'FT'
    if exterior == 'Well-Worn':
        exterior = 'WW'
    if exterior == 'Battle-Scarred':
        exterior = 'BS'
    return exterior


class Account(object):
    def __init__(self, api, currency):
        self.api = api
        self.currency = currency
        self.steamclient = None

    def ping(self):
        """Отправлять команду раз в 3-4 минуты"""
        url = f'https://market.csgo.com/api/v2/ping?key={self.api}'
        response = requests.get(url).text
        print(response)

    def get_notification(self):
        """ВАЖНО! Ключ действует ограничено время и через 60 секунд перестает приниматься сервером. При ошибке
        авторизации на сервере уведомлений сервер пришлет строку: «auth»"""

        response = requests.get(f'https://market.csgo.com/api/v2/get-ws-auth?key={self.api}')
        key = response.json()
        ws = websocket.WebSocket()
        ws.connect("wss://wsnn.dota2.net/wsn/")
        ws.send(key.get('wsAuth'))
        while True:
            data = ws.recv()
            data_json = json.loads(data)
            data_json = json.loads(data_json.get('data'))
            return data_json

    def get_balance(self):
        url = f'https://market.csgo.com/api/v2/get-money?key={self.api}'
        response = requests.get(url).text
        print(response)

    def update_inventory(self):
        """Запросить обновление кэша инвентаря (рекомендуется делать после каждого принятого трейд оффера)."""
        url = f'https://market.csgo.com/api/v2/update-inventory/?key={self.api}'
        response = requests.get(url).json()
        return response

    def my_inventory(self):
        """Получение инвентаря Steam, только те предметы, которые Вы еще не выставили на продажу."""
        url = f'https://market.csgo.com/api/v2/my-inventory?key={self.api}'
        response = requests.get(url)
        print(f'My inventory: {response}')
        response = response.json()
        if response['success']:
            return response['items']
        else:
            raise Exception('Problem in my_inventory')

    def get_items_on_sale(self):
        """
        Возможные статусы
        status = 1 — Вещь выставлена на продажу
        status = 2 — Вы продали вещь и должны ее передать боту
        status = 3 — Ожидание передачи боту купленной вами вещи от продавца
        status = 4 — Вы можете забрать купленную вещь
        Пояснения к ответам
        item_id — ID предмета в нашей системе
        status — статус предмета (см. выше)
        price — ваша цена
        position — позиция в очереди продажи (сортировка по наименьшей цене), в момент покупки выбирается самый дешевый
        предмет
        bot_id — ID бота, на котором находится предмет в статусе 4
        assetid — ID предмета в инвентаре бота
        left — Времени осталось на передачу предмета, после этого операция будет отменена и деньги вернутся покупателю.
        Будут начислены штрафные баллы
        """
        url = f'https://market.csgo.com/api/v2/items?key={self.api}'
        response = requests.get(url).json()
        return response['items']

    def get_sell_history(self, start_date, end_date):
        """ date - timestamp"""
        url = f'https://market.csgo.com/api/OperationHistory/{start_date}/{end_date}/?key={self.api}'
        response = requests.get(url)
        print(url)
        if response.status_code != 200:
            print(response)
        response = response.json()
        if response['success'] is True:
            return response['history']
        else:
            return Exception('Ошибка в get_sell_history')

    def remove_all_from_sale(self):
        url = f'https://market.csgo.com/api/v2/remove-all-from-sale?key={self.api}'
        response = requests.get(url).json()
        print(response)

    def add_to_sale(self, itemid, price):
        """
        [id] — id предмета в Steam, можно найти в описании вещей своего инвентаря в стиме.
        [price] — сумма, целое число (1 USD=1000, 1 RUB=100, 1 EUR=1000)
        [currency] — валюта (RUB, USD, EUR) дополнительная проверка, если будет указана не равная текущей установленной
        в вашем аккаунте, покупка не произойдет. Это защита от потери денег в случае, если вы сменили валюту на вашем
        аккаунте и забыли про API
        """
        url = f'https://market.csgo.com/api/v2/add-to-sale?key={self.api}&id={itemid}&price={price}&cur={self.currency}'
        response = requests.get(url)
        print(response)
        response = response.json()
        print(response)

    def set_price(self, item_id, price):
        """
        [item_id] — id предмета в Steam, можно найти в описании вещей своего инвентаря в стиме.
        [price] — сумма, целое число (1 USD=1000, 1 RUB=100, 1 EUR=1000), если указать 0 предмет будет снят с продажи
        [currency] — валюта (RUB, USD, EUR) дополнительная проверка, если будет указана неравная текущей установленной
        покупка не произойдет.
        """
        url = f'https://market.csgo.com/api/v2/set-price?key={self.api}&item_id={item_id}&price={price}&cur=' \
              f'{self.currency}'
        response = requests.get(url).json()
        print(response)

    def trades(self):
        """
        Получить список трейд офферов, которые в данный момент были высланы Маркетом на Ваш аккаунт и ожидают
        подтверждения в Steam.
        """
        url = f'https://market.csgo.com/api/v2/trades/?key={self.api}'
        response = requests.get(url).json()
        print(response)

    def trade_request_give_p2p_all(self):
        """Возвращает данные для создания всех трейдов (только для CS:GO, Dota2, Rust и TF2)"""
        url = f'https://market.csgo.com/api/v2/trade-request-give-p2p-all?key={self.api}'
        response = requests.get(url)
        if response.status_code != 200:
            raise (Exception(f'Get trades status code: {response.status_code}'))
        response = response.json()
        success = response.get('success')
        if not success:
            error = response.get('error')
            if error == 'nothing':
                return []
            else:
                raise Exception(error)
        else:
            return response['offers']

    @staticmethod
    def make_offer(self, items_from_me, items_from_them, trade_offer_url, message, case_sensitive):
        """Нужна авторизация в Steam"""
        self.steamclient.make_offer_with_url(items_from_me, items_from_them, trade_offer_url, message, case_sensitive)

    @staticmethod
    def generate_link_for_min_price(names):
        link = '&list_hash_name[]={}' * len(names)
        link = link.format(*names)
        return link

    def search_item_by_hash_name_specific(self, market_hash_name):
        url = f'https://market.csgo.com/api/v2/search-item-by-hash-name?key={self.api}&hash_name=' \
              f'{market_hash_name}'
        response = requests.get(url).json()

        return response

    @staticmethod
    def get_names(inventory_steam):
        names = []
        for key in inventory_steam:
            item_info = inventory_steam.get(key)
            market_hash_name = item_info.get('market_hash_name')
            try:
                rarity = item_info.get('tags')[4].get('localized_tag_name')
                exterior = item_info.get('tags')[5].get('localized_tag_name')
                exterior = convert_exterior(exterior)
                exterior_color = item_info.get('tags')[4].get('color')
            except TypeError:
                continue
            except IndexError:
                continue
            names.append(market_hash_name)
        lenght = len(names)
        count = lenght // 50 + 1
        return names, count

    def search_list_items_by_hash_name_all_prices(self, inventory_steam):
        names, count = self.get_names(inventory_steam)
        data_prices = {}
        for i in range(count):
            names_1 = names[50*i:50*(i+1)]
            link = self.generate_link_for_min_price(names_1)
            url = f'https://market.csgo.com/api/v2/search-list-items-by-hash-name-all?key={self.api}' + link
            response = requests.get(url).json().get('data')
            # print(json.dumps(response, sort_keys=True, indent=4))
            for item in response:
                name = item
                item = response.get(item)[0]
                classid = str(item.get('class'))
                price = str(int(item.get('price'))/100)
                data_prices[name] = price

        return data_prices

