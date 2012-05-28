from urllib import urlencode
import urllib2
import time
from hashlib import sha512
from hmac import HMAC
import base64
import json

def get_nonce():
    return int(time.time()*100000)

def sign_data(secret, data):
    return base64.b64encode(str(HMAC(secret, data, sha512).digest()))
      
class requester:
    def __init__(self, auth_key, auth_secret, url=None):
        self.auth_key = auth_key
        self.auth_secret = base64.b64decode(auth_secret)
        self.url = url or "https://mtgox.com/api/0/"
        
    def build_query(self, req={}):
        req["nonce"] = get_nonce()
        post_data = urlencode(req)
        headers = {}
        headers["User-Agent"] = "GoxApi"
        headers["Rest-Key"] = self.auth_key
        headers["Rest-Sign"] = sign_data(self.auth_secret, post_data)
        return (post_data, headers)
        
    def perform(self, path, args):
        data, headers = self.build_query(args)
        req = urllib2.Request(self.url+path, data, headers)
        res = urllib2.urlopen(req, data)
        return json.load(res)

class api():
    def __init__(self, site=None):
        self.maxp = 100
        self.minp = 0.1
        self.maxq   = 1000
        self.minq   = 0
        self.site = (site or 'mtgox').strip().lower()
        if self.site in ['mtgox','bitfl']:
            # separate the truly secret from the open API specs
            s = __import__('secrets.'+self.site) # will s then be a temporary variable?
            self.a = __import__('api.'+self.site)
        self.r = requester(auth_key=s.key, auth_secret=s.secret, url=self.a.url)

    def info(param=None):
        data = self.r.perform(path = self.a.path['info'], args={})
        if param and param in data:
            return data[param]
        return data

    def trade(quantity=None, price=0, direction=None):
        if ( self.minq<quantity<=self.maxq and self.minp<=price<=self.maxp
               and direction in ['buy','sell'] ):
            return self.r.perform(path = self.a.path[direction], 
                                  args = self.a.args(direction=direction, quantity=quantity, price=price))
    def buy(quantity=None,price=0):
        return trade(quantity=quantity, price=price, direction='buy')
    def sell(quantity=None,price=0):
        return trade(quantity=quantity, price=price, direction='sell')



def test():
    from pprint import pprint
    import secrets.mtgox as s
    import api.mtgox as a
    r = requester(auth_key=s.key, auth_secret=s.secret, url=a.url)
    pprint(r.perform(path = a.path['info'], args={}))
    
def test1():
    from pprint import pprint
    import secrets.mtgox as s
    import api.mtgox as a
    r = requester(auth_key=s.key, auth_secret=s.secret, url=a.url1)
    pprint(r.perform(path = a.path1['ticker'], args={}))

