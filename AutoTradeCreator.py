import sqlite3
import time

import steampy.models
from bs4 import BeautifulSoup

from utils import ApiTM, SteamPrice


def get_trades_from_tm():
    trades = account.trade_request_give_p2p_all()
    return trades


def create_trade(trade_info):
    partner = trade_info['partner']
    token = trade_info['token']
    message = trade_info['tradeoffermessage']
    items = trade_info['items']
    items_for_trade = []
    for item in items:
        assetid = item['assetid']
        amount = item['amount']
        items_for_trade.append(steampy.models.Asset(assetid, steampy.models.GameOptions.CS, amount))
    url = f'https://steamcommunity.com/tradeoffer/new/?partner={partner}&token={token}'
    steamAcc.steamclient.make_offer_with_url(items_for_trade, [], url, message)


def check_confirmations():
    response = steamAcc.steamclient._session.get('https://steamcommunity.com/profiles/76561198187797831/tradeoffers/sent/')
    soup = BeautifulSoup(response.text, "lxml")
    tradeofferids = soup.find_all("div", {"class": "tradeoffer"})
    ids_row = []
    ids = []
    for div in tradeofferids:
        ID = div.get('id')
        message = div.find("div", {"class": "tradeoffer_items_banner"})
        try:
            message = message.text.replace('\r', '').replace('\t', '').replace('\n', '')
        except AttributeError:
            message = "Waiting the accept from the buyer"
        print(message)
        if ID is not None:
            ids_row.append([ID, message])
    for id in ids_row:
        id[0] = id[0].replace('tradeofferid_', '')
        ids.append(id)
    print(ids)
    return ids


def confirm_confirmation(_tradeofferid: str):
    trade_offer_idf = steamAcc.steamclient.get_trade_offer(_tradeofferid)['response']['offer']['tradeofferid']
    steamAcc.steamclient._confirm_transaction(trade_offer_idf)


def confirm_all_ids():
    ids = check_confirmations()
    if ids is not None:
        for id in ids:
            tradeofferid = str(id[0])
            message = id[1]
            if message == "Awaiting Mobile Confirmation  ":
                confirm_confirmation(tradeofferid)


def add_to_checked(unique_message):
    cur = con_cache.cursor()
    query = f'INSERT INTO cache (unique_message) VALUES ("{unique_message}")'
    cur.execute(query)
    con_cache.commit()


def check_handled_items(unique_message):
    cur = con_cache.cursor()
    query = f'SELECT * FROM cache WHERE unique_message = "{unique_message}"'
    check = cur.execute(query).fetchone()
    return bool(check)


def main():
    trades = get_trades_from_tm()
    trades_for_confirm = 0
    print('Трейды: ', trades)
    for trade in trades:
        print(trade)
        if check_handled_items(trade['tradeoffermessage']):
            print('Есть в бд?:', check_handled_items(trade['tradeoffermessage']))
            continue
        trades_for_confirm += 1
        add_to_checked(trade['tradeoffermessage'])
        if 'created' not in trade:
            print('Создаю трейд')
            create_trade(trade)

    if trades_for_confirm > 0:
        time.sleep(5)
        print('Принимаю трейды')
        confirm_all_ids()



if __name__ == '__main__':
    api = '7GI98ntA4y99I7WMk26IlmkCJVWe6T9'
    account = ApiTM.Account(api, 'RUB')
    steamAcc = SteamPrice.SteamMarketMethods()
    con_cache = sqlite3.connect('db/PurchaseLogAndDuplicateCheckDB.db')
    print(steamAcc.steamclient.is_session_alive())
    while True:
        try:
            main()
        except Exception as exc:
            print('Ошибка в main', exc)
        time.sleep(10)