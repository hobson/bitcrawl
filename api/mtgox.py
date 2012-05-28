#!/usr/bin/env python
"""Module containing API specification for mtgox REST service

API specification from https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1
and https://en.bitcoin.it/wiki/MtGox/API/HTTP/v0

A key change in the API from v0 to v1 is the move from float to int. 
Floats are deprecated.

kind of field 	...divide by 	...multiply by
BTC (volume, amount) 	1E8 (100,000,000) 	0.00000001
USD (price) 	1E5 (100,000) 	0.00001
JPY (price) 	1E3 (1,000) 	0.001 

"""

url     = 'https://mtgox.com/api/0/' # "https://mtgox.com/api/0/"
url1    = 'https://mtgox.com/api/1/'
path    = {'info':'info.php', 'buy':'buyBTC.php', 'sell':'sellBTC.php'}
path1   = {'buy':'BTCUSD/private/order/add', 'ticker':'BTCUSD/public/ticker'}

def args(direction='buy',quantity=0, price=None, version=1):
    if not version==1 and quantity and direction in ['buy','sell']:
        return {}
    price = price or u''
    return {
            'type':       {'buy':'bid','sell':'ask'}[direction],
            'amount_int': unicode(int(float(quantity)*1e8)), 
            'price_int':  price,
           }

params = { 'info': 
            { 'account': 'Index', 
               'btc':'Wallets.BTC.Balance.value', # float value fields will be deprecated for value_int fields which are float*1e6
               'usd':'Wallets.USD.Balance.value', }, # float value fields will be deprecated for value_int fields which are float*1e5 (for USD, 1e3 for JPY, 1e6 for BTC)
           'ticker':
            { 'price': 'return.avg.value',
              'last':  'return.last.value',
              'high':  'return.high.value',
              'low':   'return.low.value',
            },
         }
