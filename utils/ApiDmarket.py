import pprint

import requests


def get_items(market_hash_name):
    url = 'https://api.dmarket.com/exchange/v1/market/items?'
    params = {
        'side': 'market',
        'orderBy': 'personal',
        'orderDir': 'desc',
        'title': market_hash_name,
        'priceFrom': 0,
        'priceTo': 0,
        'gameId': 'a8db',
        'types': 'dmarket',
        'limit': 100 ,
        'currency': 'USD',
        'platform': 'browser',
        'isLoggedIn': 'true'
    }
    response = requests.get(url, params).json()
    print(response['objects'][0])
    pprint.pprint(response['objects'][0])


if __name__ == '__main__':
    get_items('USP-S | Cortex (Minimal Wear)')