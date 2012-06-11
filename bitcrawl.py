#!/usr/bin/python

"""Module for crawling the web, extracting numbers, counting links and other stats

    Calculates statistics of the data gathered and plots 2-D plots.

    Standard Module Dependencies:
        argparse    ArgumentParser
        urllib      urlencode, urlopen,...
        urllib2     HTTPRedirectHandler, HTTPCookieProcessor, etc
        time        sleep
        datetime    now(), datetime.strptime(), datetime.datetime(), etc
        httplib     IncompleteRead
        numpy       
        matplotlib  pyplot.plot

    Nonstandard Module Dependencies:
        tz          Local # local time zone object definition

    TODO:
    1. deal with csv: http://www.google.com/trends/?q=bitcoin&ctab=0&geo=us&date=ytd&sort=0 , 
          <a href='/trends/viz?q=bitcoin&date=ytd&geo=us&graph=all_csv&sort=0&scale=1&sa=N'>
          other examples in comments below
    2. poll domain name registries to determine the number of domain names with "bitcoin" in them or beginning with "bit" or having "bit" and "coin" in them 
    3. build website and REST to share bitcoin trend info, several domain names saved at bustaname under shopper@tg username 
          pairbit, bitpair, coinpair, paircoin, coorbit, bitcorr, bitcoinarbitrage, etc
    4. generalize the search with AI and ML to identify good and bad trends for all common proper names--stock symbols, etc
       a) write research paper to prove it does as good a job as a human stock analyst at predicting future price movements
       b) write a browser plugin that allows a human to supervise the machine learning and identify useful/relevant quantitative data
    5. implement the indexer and search engine for the double-star question 3 in CS101 and get quant data directly from the index
    6. implement the levetshire distance algorithm from the CS101 exam for use in word-stemming and search term similarity estimate
    7. record response time of web pages as one of the stats associated with each url
    8. use historical load-time data to prioritize quickly-loading pages over defunt, slow pages (like bitcoinsonsultancy.com)

    :author: Hobson Lane dba TotalGood
    :copyright: 2012 by Hobson Lane (hobson@totalgood.com), see AUTHORS for details
    :license:   Creative Commons BY-NC-SA, see LICENSE for more details
"""

# TODO: smart import by wrapping all import statements in try: blocks
# TODO: smarter import with gracefull fallback to "pass" or simple local implementations for unavailable modules
# TODO: smartest import with pip install (setup.py install) of missing modules, if possible
# TODO: ai import with automatic, on-the-fly, python source code generation... with comments and docstrings! ;)
import datetime
import time
from tz import Local
import os
import urllib
import urllib2
import httplib
import json
from pprint import pprint
from argparse import ArgumentParser
import re
from warnings import warn
import matplotlib.pyplot as plt
from utils import size, size2, size3
import collections # .Iterable

FILEPATH=os.path.expanduser('data/bitcrawl_historical_data.json') # change this to a path you'd like to use to store data
MIN_ORDINAL=1800*365.25 # data associated with datetime ordinals smaller than this will be ignored
MAX_ORDINAL=2100*365.25 # data associated with datetime ordinals larger than this will be ignored
SAMPLE_BIAS_COMP = 0 # whether to divide variance values by N-1 (0 divides by N so that small sample sets still give 1 for Pearson self-correlation coefficient)

# Hard-coded regular expressions, keywords, and URLs for gleaning numerical data from the web
URLs={'network': 
        { 
          'url': 'http://bitcoincharts.com/about/markets-api/',
          'blocks':
            [r'<td class="label">Blocks</td><td>',          # (?<= ... )\s*
             r'[0-9]{1,9}'                               ],  # (...)
          'total_btc': # total money supply of BTC
            [r'<td class="label">Total BTC</td><td>',
             r'[0-9]{0,2}[.][0-9]{1,4}[TGMKkBb]' ], 
          'difficulty':
            [r'<td class="label">Difficulty</td><td>',
             r'[0-9]{1,10}' ], 
          'estimated': # total money supply of BTC
            [r'<td class="label">Estimated</td><td>',
             r'[0-9]{1,10}' ] ,
          'blocks':     # total money supply of BTC blocks
            [r'<td class="label">Estimated</td><td>\s*[0-9]{1,10}\s*in',
             r'[0-9]{1,10}' ] ,
          'hash_rate':     # THash/s on the entire BTC network
            [r'<td class="label">Network total</td><td>',
             r'[0-9]{0,2}[.][0-9]{1,4}' ],
          'block_rate':     # blocks/hr on the entire BTC network
            [r'<td class="label">Blocks/hour</td><td>',
             r'[0-9]{0,3}[.][0-9]{1,4}' ] } ,
    'trade': {
        'url': 'https://en.bitcoin.it/wiki/Trade',
        'visits':
            [r'has\sbeen\saccessed\s',
             r'([0-9]{1,3}[,]?){1,4}'  ] }, 
    'shop': {
        'url': 'https://en.bitcoin.it/wiki/Real_world_shops',
        'visits':
            [r'has\sbeen\saccessed\s',
             r'([0-9]{1,3}[,]?){1,4}'  ] }, 
    'bitcoin': {
        'url': 'https://en.bitcoin.it/wiki/Main_Page',
        'visits':
            [r'has\sbeen\saccessed\s',
             r'([0-9]{1,3}[,]?){1,4}'  ] },
# went "offline" sometime around May 20th
#    'consultancy': {
#        'url': 'https://bitcoinconsultancy.com/wiki/Main_Page',
#        'visits':
#            [r'has\sbeen\saccessed\s',
#             r'([0-9]{1,3}[,]?){1,4}'  ] }, 
    'mtgox':    {
        'url': 'https://mtgox.com',
        'average':
        [r'Weighted\s*Avg\s*:\s*<span>',
         r'\$[0-9]{1,2}[.][0-9]{3,6}' ],  
        'last':
        [r'Last\s*price\s*:\s*<span>',
         r'\$[0-9]{1,2}[.][0-9]{3,6}' ],
        'high':
        [r'High\s*:\s*<span>',
         r'\$[0-9]{1,2}[.][0-9]{3,6}' ],
        'low':
        [r'Low\s*:\s*<span>',
         r'\$[0-9]{1,2}[.][0-9]{3,6}' ],
        'volume':
        [r'Volume\s*:\s*<span>',
         r'[0-9,]{1,9}' ] },
    'virwox': {
        'url': 'https://www.virwox.com/',
        'volume':  # 24 hr volume
        # (?s) means to match '\n' with dot ('.*' or '.*?')
        [r"(?s)<fieldset>\s*<legend>\s*Trading\s*Volume\s*\(SLL\)\s*</legend>\s*<table.*?>\s*<tr.*?>\s*<td>\s*<b>\s*24\s*[Hh]ours\s*[:]?\s*</b>\s*</td>\s*<td>", 
         r'[0-9,]{1,12}'],
        'SLLperUSD_ask': 
        [r"<tr.*?>USD/SLL</th><td.*?'buy'.*?>",
         r'[0-9]{1,6}[.]?[0-9]{0,3}'],
        'SLLperUSD_bid': 
        [r"<tr.*?>USD/SLL</th.*?>\s*<td.*?'buy'.*?>.*?</td>\s*<td.*?'sell'.*?>",
         r'[0-9]{1,6}[.]?[0-9]{0,3}'],
        'BTCperSLL_ask': 
        [r"<tr.*?><th.*?>BTC/SLL\s*</th>\s*<td\s*class\s*=\s*'buy'\s*width=\s*'33%'\s*>\s*", # TODO: generalize column/row/element extractors
         r'[0-9]{1,6}[.]?[0-9]{0,3}'],
        'BTCperSLL_bid': 
        [r"<tr.*?>BTC/SLL</th.*?>\s*<td.*?'buy'.*?>.*?</td>\s*<td.*?'sell'.*?>",
         r'[0-9]{1,6}[.]?[0-9]{0,3}'] },
    'cointron': {  
        'url': 'http://coinotron.com/coinotron/AccountServlet?action=home', # miner doesn't follow redirects like a browser so must use full URL
        'hash_rate': 
        [r'<tr.*?>\s*<td.*?>\s*BTC\s*</td>\s*<td.*?>\s*',
         r'[0-9]{1,3}[.][0-9]{1,4}\s*[TMG]H',
         r'</td>'], # unused suffix
        'miners': 
        [r'(?s)<tr.*?>\s*<td.*?>\s*BTC\s*</td>\s*<td.*?>\s*[0-9]{1,3}[.][0-9]{1,4}\s*[TGM]?H\s*</td>\s*<td.*?>'
         r'[0-9]{1,4}\s*[BbMmKk]?',
         r'</td>'], # unused suffix
        'hash_rate_LTC':  # lightcoin
        [r'<tr.*?>\s*<td.*?>\s*LTC\s*</td>\s*<td.*?>\s*',
         r'[0-9]{1,3}[.][0-9]{1,4}\s*[TMG]H',
         r'</td>'], # unused suffix
        'miners_LTC': 
        [r'(?s)<tr.*?>\s*<td.*?>\s*LTC\s*</td>\s*<td.*?>\s*[0-9]{1,3}[.][0-9]{1,4}\s*[TGM]?H\s*</td>\s*<td.*?>',
         r'[0-9]{1,4}\s*[BbMmKk]?',
         r'</td>'], # unused suffix
        'hash_rate_SC':  # scamcoin
        [r'<tr.*?>\s*<td.*?>\s*SC\s*</td>\s*<td.*?>\s*',
         r'[0-9]{1,3}[.][0-9]{1,4}\s*[TMG]H',
         r'</td>'], # unused suffix
        'miners_SC': 
        [r'(?s)<tr.*?>\s*<td.*?>\s*SC\s*</td>\s*<td.*?>\s*[0-9]{1,3}[.][0-9]{1,4}\s*[TGM]?H\s*</td>\s*<td.*?>',
         r'[0-9]{1,4}\s*[BbMmKk]?',
         r'</td>'] }, # unused suffix
    }

def get_seeds(path='data/bitsites.txt'):
    """Read in seed urls from a flatfile (newline delimitted)

    >>> print len(get_seeds())
    68
    """
    try: 
        f = open(path,'r')
    except:
        print 'Unable to find the file "'+path+'".'
        return []
    s = f.read()
    return s.split('\n') # FIXME: what about '\r\n' in Windows

# Additional seed data URLs
# TODO: function to extract/process CSV
#Historic Trade Data available from bitcoincharts and not yet mined:
#Trade data is available as CSV, delayed by approx. 15 minutes.
#http://bitcoincharts.com/t/trades.csv?symbol=SYMBOL[&start=UNIXTIME][&end=UNIXTIME]
#returns CSV:
#unixtime,price,amount
#Without start or end set it'll return the last few days (this might change!).
#Examples
#Latest mtgoxUSD trades:
#http://bitcoincharts.com/t/trades.csv?symbol=mtgoxUSD
#All bcmPPUSD trades:
#http://bitcoincharts.com/t/trades.csv?symbol=bcmPPUSD&start=0
#btcexYAD trades from a range:
#http://bitcoincharts.com/t/trades.csv?symbol=btcexYAD&start=1303000000&end=1303100000
#Telnet interface
#There is an experimental telnet streaming interface on TCP port 27007.
#This service is strictly for personal use. Do not assume this data to be 100% accurate or write trading bots that rely on it.

class Bot:
    """A browser session that follows redirects and maintains cookies.

    TODO: 
        allow specification of USER_AGENT, COOKIE_FILE, REFERRER_PAGE
        if possible should use the get_page() code from the CS101 examples to show "relevance" for the contest

    Examples:
    >>> len(Bot().GET('http://totalgood.com',retries=1,delay=0,len=100))
    100
    """

    def __init__(self):
        self.retries     = 0
        self.response    = ''
        self.params      = ''
        self.url         = ''
        redirecter  = urllib2.HTTPRedirectHandler()
        cookies     = urllib2.HTTPCookieProcessor()
        self.opener = urllib2.build_opener(redirecter, cookies)
    def GET(self, url, retries=2, delay=2, len=1e7):
        self.retries = max(self.retries, retries)
        # don't wait less than 0.1 s or longer than 1 hr when retrying a network connection
        delay = min(max(delay,0.1),3600)
        file_object, datastr = None, ''
        try:
            print 'opening ', url
            file_object = self.opener.open(url)
        # build_opener object doesn't handle 404 errors, etc !!! 
        # TODO: put all these error handlers into our Bot class
        except httplib.IncompleteRead, e:
            print "HTTP read for URL '"+url+"' was incomplete: %d" % e.code
        except urllib2.HTTPError, e:
            print "HTTP error for URL '"+url+"': %d" % e.code
        except httplib.BadStatusLine, e:
            print "HTTP bad status link for URL '"+url+"': %d" % e.code
        except urllib2.URLError, e:
            print "Network error for URL '"+url+"': %s" % e.reason.args[1]
        if not file_object:
            # retry
            if retries:
                print "Waiting "+str(delay)+" seconds before retrying network connection for URL '"+url+"'..."
                print "Retries left = "+str(retries)
                time.sleep(delay)
                print "Retrying network connection for URL '"+url+"'."
                return self.GET(url,retries-1)
            print "Exceeded maximum number of Network error retries."
        else:
            try:
                datastr = file_object.read(len) # should populate datastr with an empty string if the file_object is invalid, right?
            except:
                print('Error reading http GET response from url '+repr(url)+
                      ' after at most '+str(self.retries)+' retries.')
        return datastr
    def POST(self, url, params):
        self.url    = url
        self.params = urllib.urlencode(params)
        self.response = self.opener.open(url, self.params ).read()
        return self.response

def get_page(url):
    """Retrieve a webpage from the given url (don't follow redirects or use cookies, though)

    >>> print 1000 < len(get_page('http://google.com')) < 1E7
    True
    """
    try:
        return urllib.urlopen(url).read()
    except:
        return ''

# These extensive, complicated datetime regexes patterns don't work!
QUANT_PATTERNS = dict(
    # HL: added some less common field/column separators: colon, vertical_bar
    SEP                  = r'\s*[\s,;\|:]\s*', 
    DATE_SEP             = r'\s*[\s,;\|\-\:\_\/]\s*',
    # based on DATE_SEP (with \s !!) ORed with case insensitive connecting words like "to" and "'till"
    RANGE_SEP            = r"(?i)\s*(?:before|after|then|(?:(?:un)?(?:\')?til)|(?:(?:to)?[\s,;\|\-\:\_\/]{1,2}))\s*", 
    TIME_SEP             = r'\s*[\s,;\|\-\:\_]\s*',
    # HL: added sign, spacing, & exponential notation: 1.2E3 or +1.2 e -3
    FLOAT                = r'[+-]?\d+(?:\.\d+)?(?:\s?[eE]\s?[+-]?\d+)?', 
    FLOAT_NONEG          =  r'[+]?\d+(?:\.\d+)?(?:\s?[eE]\s?[+-]?\d+)?', 
    FLOAT_NOSIGN         =      r'\d+(?:\.\d+)?(?:\s?[eE]\s?[+-]?\d+)?', 
    # HL: got rid of exponential notation with an E and added x10^-4 or *10^23
    FLOAT_NOE            = r'[+-]?\d+(?:\.\d+)?(?:\s?[xX*]10\s?\^\s?[+-]?\d+)?', 
    FLOAT_NONEG_NOE      =  r'[+]?\d+(?:\.\d+)?(?:\s?[xX*]10\s?\^\s?[+-]?\d+)?', 
    FLOAT_NOSIGN_NOE     =      r'\d+(?:\.\d+)?(?:\s?[xX*]10\s?\^\s?[+-]?\d+)?', 
    # HL: added sign and exponential notation: +1e6 -100 e +3
    INT                  = r'[+-]?\d+(?:\s?[eE]\s?[+]?\d+)?',
    INT_NONEG            =  r'[+]?\d+(?:\s?[eE]\s?[+]?\d+)?',
    INT_NOSIGN           =      r'\d+(?:\s?[eE]\s?[+]?\d+)?', # HL: exponents should always be allowed a sign 
    INT_NOSIGN_2DIGIT    = r'\d\d',
    INT_NOSIGN_4DIGIT    = r'\d\d\d\d',
    INT_NOSIGN_2OR4DIGIT = r'(?:\d\d){1,2}',
    YEAR                 = r'(?i)(?:1[0-9]|2[012]|[1-9])?\d?\d(?:\s?AD|BC)?',  # 2299 BC - 2299 AD, no sign
    MONTH                = r'[01]\d|\d',   # 01-12
    DAY         = r'[0-2]\d|3[01]|[1-9]',     # 01-31 or 1-9
    HOUR        = r'[0-1]\d|2[0-4]|\d',    # 01-24 or 0-9
    MINUTE      = r'[0-5]\d',           # 00-59
    SECOND      = r'[0-5]\d(?:\.\d+)?', # 00-59
    )

DATE_PATTERN = re.compile(r"""
        (?P<y>%(YEAR)s)%(DATE_SEP)s
        (?P<mon>%(MONTH)s)%(DATE_SEP)s
        (?P<d>%(DAY)s)
""" % QUANT_PATTERNS, re.X)

TIME_PATTERN = re.compile(r"""
        (?P<h>%(HOUR)s)%(TIME_SEP)s
        (?P<m>%(MINUTE)s)(?:%(TIME_SEP)s
        (?P<s>%(SECOND)s))? 
""" % QUANT_PATTERNS, re.X)


DATETIME_PATTERN = re.compile(r'(?P<date>'+DATE_PATTERN.pattern+
                              r')(?:'+QUANT_PATTERNS['DATE_SEP']+
                              r')?(?P<time>'+TIME_PATTERN.pattern+r')?', re.X)

def zero_if_none(x):
    if not x:
        return 0
    return x

def parse_date(s):
    """Nested regular expressions to proces date-time strings

    >>> parse_date('2001-2-3 4:56:54.123456789')
    datetime.datetime(2001, 2, 3, 4, 56, 54, 123456)
    Values for seconds or minutes that exceed 60 are ignored
    >>> parse_date('2001-2-3 4:56:78.910')
    datetime.datetime(2001, 2, 3, 4, 56)
    >>> parse_date('2012-04-20 23:59:00')
    datetime.datetime(2012, 4, 20, 23, 59)
    >>> parse_date('1776-07-04')
    datetime.datetime(1776, 7, 4, 23)
    >>> parse_date('2012-04-12 13:34')
    datetime.datetime(2012, 4, 20, 13, 34)
    """
    from math import floor

    mo=DATETIME_PATTERN.search(s)
    if mo:
        y = mo.group('y') or 0
        if len(y) == 2:
            if y[0] == '0':
                y = int(y) + 2000
#            else:
#                y = int(y)
#                if y > 20 and y < 100:
#                    y = y + 1900
        y = int(y)
        mon = int(zero_if_none(mo.group('mon')))
        d = int(zero_if_none(mo.group('d')))
        h = int(zero_if_none(mo.group('h')))
        m = int(zero_if_none(mo.group('m')))
        s_f = float(zero_if_none(mo.group('s')))
        s = int(floor(s_f))
        us = int((s_f-s)*1000000.0)
        return datetime.datetime(y,mon,d,h,m,s,us)
    else:
        raise ValueError("Date time string not recognizeable or not within a valid date range (2199 BC to 2199 AD): %s" % s)

def parse_time(s):
    """Nested regular expressions to time strings

    >>> parse_time('4:56:54.123456789')
    datetime.time(4, 56, 54, 123456)
    """
    from math import floor

    mo=TIME_PATTERN.search(s)
    if mo:
        h = int(zero_if_none(mo.group('h')))
        m = int(zero_if_none(mo.group('m')))
        s_f = float(zero_if_none(mo.group('s')))
        s = int(floor(s_f))
        us = int((s_f-s)*1000000.0)
        # FIXME: parse the AM/PM bit
        return datetime.time(h,m,s,us)
    else:
        raise ValueError("Time string not recognizeable or not within a valid date range (00:00:00 to 24:00:00): %s" % s)

def get_next_target(page):
    """Extract a URL from a string (HTML for a webpage)

    >>> print get_next_target('hello <a href="world">.</a>')
    ('world', 20)
    """
    start_link = page.find('<a href=')
    if start_link == -1: 
        return None, 0
    start_quote = page.find('"', start_link)
    end_quote = page.find('"', start_quote + 1)
    url = page[start_quote + 1:end_quote]
    return url, end_quote

def union(p,q):
    for e in q:
        if e not in p:
            p.append(e)

def interp_multicol(lol,newx=None):
    """Linearly interpolate mulitple columns of data. First column is independent variable.

    >>> interp_multicol([range(6),[float(x)**1.5 for x in range(6)],range(3,-3,-1)],[0.4*x for x in range(15)])
    """
    #print lol
    #lol = make_wide(lol)
    lol = transpose_lists(lol)
    x=lol[0]
    #print lol[1:]
    for c,col in enumerate(lol[1:]):
        #print c,col,x,newx
        lol[c+1] = interpolate(x,col,newx)

def interpolate(x,y,newx=None,method='linear',verbose=True):
    """
    Interpolate y for newx.

    y and newx must be the same length

    >>> interpolate([0,1,2],[5,6,7],[-.5,0,.33,.66,1.,1.33,1.66,2,2.5])
    [5.0, 5.0, 5.33, 5.66, 6.0, 6.33, 6.66, 7.0, 7.0]
    >>> interpolate([0,3,4],[1,2,3])
    [1.0, 1.6666666666666665, 3.0]
    """
    # TODO: walk the dimensions of the lists, doing a size() to find which 
    #       dimensions correspond  (x <--> y) so that the interpolation vector
    #       lengths match
    N = len(x)
    if not len(y) == N:
        raise ValueError('Interpolated lists must be the same length, even if the dependent variable (y) has more dimensions')
    newy = []
    if isinstance(x[0],(float,int,str)) and isinstance(y[0],(list,tuple)):
        if verbose:
            print 'interpolate() is trying for size(x)='+repr(size(x))+'  size(y)='+repr(size(y2))+'size(newx)='+repr(size(newx))
        x2 = []
        for j in range(len(y[0])):
            x2 += []
            for i,x2 in enumerate(x):
                x2[i][j] = x
        return interpolate(x2,y,newx,method,verbose) # FIXME: doesn't work for 2-D y and 1-D x
        for j in range(len(y[0])):
            y1=[]
            for i in range(len(y)):
                if j<len(y[i]):
                    y1 += y[i][j]
            newy += interpolate(x=x, y=y1, newx=newx, method=method, verbose=verbose)
        return newy
    elif isinstance(x[0],(list,tuple)) and isinstance(y[0],(list,tuple)):
        # TODO: check the length of x[0] and y[0] to see which dimension in y corresponds to x
        return [ interpolate(x1,y1,newx,method,verbose=verbose) for x1,y1 in zip(x,y) ]
    # TODO: now that we're at the innermost dimension of the 2 lists, we need
    #       to check that the length of the x and y and/or newx lists match
    # TODO: sort x,y (together as pairs of tuples) before interpolating, then unsort when done
    if not newx:
        N = max(len(x),2)
        newx = [float(x1*(x[-1]-x[0]))/(N-1)+x[0] for x1 in range(len(x))]
    #if newx and len(newx)>1:
        #print make_wide(newx)
    N=len(newx)
    if not len(x)==len(y):
        raise ValueError("Can't interpolate() for size(x)="+repr(size(x))+'  size(y)='+repr(size(y))+'size(newx)='+repr(size(newx)))
    if method.lower().startswith('lin'):
        i, j, x0, y0 = 0, 0, newx[0], y[0]
        while i < len(x) and j<N:
            # no back-in-time extrapolation... yet
            if x[i] <= newx[j]:
                x0, y0 = float(x[i]), float(y[i])
                i += 1
            else:
                if x[i] != x0: # check for divide by zero
                    newy.append((float(y[i])-y0)*(float(newx[j])-x0)/(float(x[i])-x0)+y0)
                else: #nearest neighbor is fine if interpolation distance is zero!
                    newy.append(float(y0))
#                if j>=N-1: # we've finished the last newx value
#                    break
                j = j+1
        # no extrapolation, assume time stops ;)
        for j in range(j,N):
            newy.append(float(y[-1]))
    else:
        raise(NotImplementedError('Interpolation method not implemented'))
    return newy


def var2(listoflist):# assuming equal datetime intervals
    """
    :Author: Nat
    """
    averagelist=[]
    variance =0
    for element in listoflist:
        #print 'element=',element
        #print 'element[1]=',element[1]
        averagelist.append(element[1])# appends average value from listoflist
    sumlist = sum(averagelist)
    meanavg = sumlist/len(averagelist)#mean of the list containing all the 'average' data
    #print'meanavg=',meanavg
    for e in averagelist:
        variance = variance + (e - meanavg)**2
    variance = variance/len(averagelist)
    return variance

def wikipedia_view_rates(articles=['Bitcoin','James_Surowiecki'],verbose=False,names=''):
    # TODO: make this a 2-D array with the article title and various view rate stats for each element in articles
    dat = dict()
    if not names:
        name = 'wikipedia_view_rate'
    elif isinstance(names,str):
        name=names
    elif isinstance(names,list) and len(names)==len(articles):
        for i,article in enumerate(articles):
            dat[name[i]] = wikipedia_view_rate(article=article,verbose=verbose)
        return dat

    for article in articles:
        #if verbose:
        print 'Checking wikipedia view rate for "'+article+'"'
        dat[name+'_'+article] = wikipedia_view_rate(article=article,verbose=verbose)
    return dat

def wikipedia_view_rate(article='Bitcoin',verbose=False):
    return mine_data(url='http://stats.grok.se/en/latest/'+article,
                     prefixes=r'[Hh]as\sbeen\sviewed\s',
                     regexes=r'[0-9,]{1,12}',
                     names='view_rate_'+article,
                     verbose=verbose) 

def get_all_links(page):
    links = []
    while True:
        url,endpos = get_next_target(page)
        if url:
            links.append(url)
            page = page[endpos:]
        else:
            break
    return links # could use set() to filter out duplicates

# TODO: compute and return other statistics about the page associated with the page:
#       1. page length
#       2. keywords & frequencies (use the CS101 multi-word indexer?)
#       3. meta data accuracy
#       4. number of links
#       5. depth
#       6. number of broken lengths
#       7. number of spelling errors and/or some grammar errors (the ones that are easy to detect reliably)
def get_links(url='https://en.bitcoin.it/wiki/Trade',max_depth=1,max_breadth=1e6,max_links=1e6,verbose=False,name=''):
    """ Return a list of all the urls linked to from a page, exploring the graph to the specified depth.

        uses the get_page() get_all_links() functions from the early part of CS101, should be updated using more recent CS101 code

        TODO: 
            set default url if not url
            BUG: tries to browse to weird URLs and bookmarks, e.g. "href=#Printing"
            need to count stats like how many are local and how many unique second and top level domain names there are

    """
    tocrawl = [url]
    crawled = []
    depthtocrawl = [0]*len(tocrawl)
    depth = 0
    page = tocrawl.pop()
    depth = depthtocrawl.pop()
    links = 0
    if verbose:
        print 'Counting links by crawling URL "'+url+'" to a depth of '+str(max_depth)+'...'
    if not name:
        name = 'data'
    while depth<=max_depth and links<max_links:
        links += 1
        if page not in crawled:
            i0=len(tocrawl)
            link_urls = set(get_all_links(get_page(page))) # set() makes sure all links are unique
            union(tocrawl, link_urls)
            if verbose:
                print 'Retrieved '+str(len(link_urls))+' links at "'+ page + '"'
            crawled.append(page)
            for i in range(i0,len(tocrawl)):
                depthtocrawl.append(depth+1)
        if not tocrawl: break
        page  = tocrawl.pop(0) # FIFO to insure breadth first search
        depth = depthtocrawl.pop(0) # FIFO
    dt = datetime.datetime.now(tz=Local)
    return {name:{'datetime':str(dt),'url':url,'links':len(crawled),'depth':max_depth}}

# TODO: set default url if not url
def rest_json(url='https://api.bitfloor.com/book/L2/1',verbose=False):
    if verbose:
        print 'Getting REST data from URL "'+url+'" ...'
    data_str = Bot().GET(url)
    dt = datetime.datetime.now(tz=Local)
    if verbose:
        print 'Retrieved a '+str(len(data_str))+'-character JSON string at '+ str(dt)
    if len(data_str)>2:
        data     = json.loads( data_str )
        data['datetime']=str(dt)
        data['url']=url
        data['len']=len(data_str)
        # this name needs to reflect the URL specified as an input rather than a hard-coded name
        if verbose:
            print data
        return data
    return None


# FIXME: ANTIIDIOM
#def readable(path):
#    try:
#        f = open(path,'r')
#        # return f # but this makes readable() just like an f = open(... wrapped in a try
#        f.close()
#        return True
#    except:
#        return False

def file_is_readable(file):
    with open(file) as fp:
        return fp.readline()
    # unfortunately the file will close when this returns so you can't just keep reading it
    # better to do this within the code where this was called to continue using fp while it's open

# VERY ANTI-IDIOMATIC
def updateable(path,initial_content='',min_size=0):
    if initial_content:
        min_size = max(min_size,len(initial_content))
    #TODO: use os.path_exists instead of try
    if not min_size:
        try:
            f = open(path,'r+') # w = create the file if it doesn't already exist, truncate to zero length if it does
        except:
            return False
        f.close()
        return True
    else:
        if file_is_readable(path): # don't open for writing because that will create and truncate it
            try:
                f = open(path,'r+')
            except:
                return False
            f.seek(0,2)  # go to position 0 relative to 2=EOF (1=current, 0=begin)
            if f.tell()>=min_size:
                f.close()
                return True
            else:
                f.close()
                if initial_content:
                    f = open(path,'w')
                    f.write(initial_content)
                    f.close()
                    return True
        else:
            try:
                f = open(path,'w')
            except:
                return False
            if initial_content:
                f = open(path,'w')
                f.write(initial_content)
            f.close()
            return True
        return False

def parse_index(s):
    """Parses an array/list/matrix index string.
    
    >>> parse_index('[1][2]')
    [1, 2]
    >>> parse_index('[3][2][1]')  # FIXME, commas and parentheses don't work !
    [3, 2, 1]
    """
    #return (0)
    mo=re.match(r'[\[\(\{]+\s*(\d(?:\s*[:]\s*\d){0,2})+(?:\s*[\[\(\{\]\)\},; \t]\s*)+(\d(?:\s*[:]\s*\d){0,2})+\s*[\]\)\}]+',s)
    # FIXME: needs to subparse the slice notation, e.g. '1:2:3'
    # this only handles single indexes
    return [int(s) for s in mo.groups()]

def parse_query(q):
    """Parse query string identifing records in bitcrawl_historical_data.json

    Returns a 3 equal-length lists
        sites  = a name (key) for the webpage where data was originally found
        values = the key for the values on the webpages identified by sites
        datetimes = list of lists with the datetimes for which data is desired

    Friendlier interface for bycol_key() which is turn used for
    forecast_data() & plot_data()

    >>> parse_query('bitfloor.bids[0][0] date:2012-04-12 13:35')
    (['bitfloor'], ['bids'],...)
    """
    # print 'query', q
    if q and isinstance(q,(list,set)): # a tuple is the return value for a single query string!
        retval = [ parse_query(s) for s in q ]
        retval = transpose_lists(retval)
        return retval[0], retval[1], retval[2]
    sites = []
    values = []
    datetimes = []
    if q and isinstance(q,str):
        # TODO: generalize query parsing with regex
        tok = q.split(' ') # only space may separate query terms from tags
        u,v = tok[0].split('.')
        sites.append(u)
        # FIXME: this will break if different types of braces are used in a row
        n = max(v.find('['),v.find('('),v.find('{'))
        if n>-1:
            values.append(v[:n])
            indexes=parse_index(v[n:])
        else:
            values.append(v)
        datetimes.append([])
        i = 1 # the first token must always be the site.value "URI"
        while i < len(tok):
            t = tok[i]
            i += 1
            # print 'tok',tok
            if t.lower().startswith('date') and len(t)>5 and t[4] in ":= \t|,;":
                if i<len(tok):
                    if isinstance(parse_time(tok[i]),datetime.time):
                        t += ' '+str(tok[i])
                        i += 1
                datetimes[-1].append(parse_date(t[6:]))
                
    # FIXME: this is no longer required for auto-correlation, unless you just want to double-check the algorithm
    #sites = [sites,sites] if isinstance(sites,str) else sites
    #values = [values,values] if isinstance(values,str) else values

#    print '-'*10
#    print sites
#    print '-'*10
#    print values
#    print '-'*10
#    print datetimes
#    print '-'*10
    return [sites[0], values[0], datetimes]
    #return (s[0] for s in sitevalues, datetimes
#    warn('Unable to identify the sites and values that query string attempted to retrieve. '+
#        ' \n query  = '+ str(q)+
#        ' \n sites  = '+ str(sites)+
#        ' \n values = '+ str(values) )

# TODO: incoporate interpolation 
def retrieve_data(sites='mtgox',values='average', datetimes=None, filepath=None, verbose=True):
    """
    Retrieve data from bitcrawl_historical_data.json for sites and values specified

    >>> retrieve_data('mtgox','last', ['2012-04-12 13:34','2012-04-15 13:35'])
    [[734605.0, 734606.0, 734607.0, 734608.0],
     [4.8833, 4.85660013796317, 4.890036645675644, 4.975431555147281]]
    Surprisingly this doesn't retrieve the volumes, just the prices for bf bids
    And the dimensions seem weird
    >>> retrieve_data('bitfloor','bids', ['2012-04-12 13:34','2012-04-12 13:35'])
    [[734605.0], [[[4.88], [4.87], [4.86], ... [4.6], [4.59], [4.58]]]]
    """
    if isinstance(sites,list) and isinstance(values,list):
        if verbose:
            print 'sites and values are lists'
        return     [ retrieve_data(s,v)      for s,v in zip(sites,values) ]
    if isinstance(sites,list) and isinstance(values, str):
        return [ retrieve_data(s,values) for s   in sites             ]
    if isinstance(sites, str) and isinstance(values,list):
        return [ retrieve_data(sites, v) for v   in values            ]
    rows = []
    if isinstance(values,str) and isinstance(sites,str):
        if verbose:
            print 'retrieving a single data series, ('+sites+','+values+').'
        # very inefficient to reload data with every time series retrieved
        data = load_json(filepath, verbose=False) # None filepath loads data from default path
        if not data:
            warn('Historical data could not be loaded from '+repr(filepath))
            return []
        rows = byrow_key(data, name=sites, yname=values, xname='datetime', verbose=False)
    else:
        warn('Invalid site key '+repr(sites)+', or value key '+repr(values))
        return None
    if not (isinstance(rows,list) or not isinstance(rows[0],list)): # should always be an Nx2 matrix with each element either a value or a list of M values
        warn('Unable to find matching data of type '+repr(type(columns))+
             ' using site key '+repr(sites)+' and value key '+repr(values))
        return None
    NM = size(rows)
    if verbose:
        print "Retrieved an array of historical data records size",NM
    if (not rows or not isinstance(NM,(list,tuple)) or len(NM)<2 or
                   any([nm<1 for nm in NM]) ):
        print "Retrieved 1 or fewer data points, which is unusual."
        return rows

    t = []
    if not datetimes:
        # interpolate columns data to create regularly-space, e.g.daily or bi-daily, values
        t = [float(x) for x in range(int(min(rows[0])),
                                     int(max(rows[0]))+1)]
    else:
        t = datetime2float(datetimes) # this will be a float or list of floats
    rows[1] = interpolate(x=rows[0], y=rows[1], newx=t, verbose=verbose)
    rows[0] = t

# this can never happen
#    i=1
#    while i<len(sites):
#        s,v = sites[i],values[i]
#        rows2 = byrow_key(data,name=s,yname=v,xname='datetime')
#        if len(rows2)<2: 
#            break
#        # interpolate the new data to line up in time with the original data
#        #print len(cols2[0]), len(cols2[1]),len(columns[0])
#        newrow = interpolate(rows2[0], rows2[1], newx=t, verbose=verbose)
#        #print newrow
#        #print columns
#        rows.append(newrow)
#        #print columns
#        i += 1
    return rows

def query_data(q,filepath=None):
    """Retrieve data from bitcrawl_historical_data.json that matches a query string

    Friendlier interface for bycol_key() which is turn used for
    forecast_data() & plot_data()

    >>> query_data('bitfloor.bids[0][0] date:2012-04-12 13:35')
    4.88
    """
    sites, values, datetimes = parse_query(q)
    return retrieve_data(sites=sites, values=values, 
                         datetimes=datetimes, filepath=filepath)



def bycol_key(data, name='mtgox', yname='average', xname='datetime',verbose=False):#function for returning values given a key of the dictionary data
    columns =[] # list of pairs of values
    # loops thru each data item in the list
    if not data:
        warn('No data provided')
        return []
    for record in data:
        # if this record (dict) contains the named key (e.g. 'mtgox')
        #print 'looking for '+name
        if name in record:
            #print '-------- found '+name
            keyrecord = record[name]
            #print 'keyrecord=',keyrecord
            #print 'type(keyrecord)=',type(keyrecord)
            #print 'size(kr)=',size(keyrecord)
            # is the requested x data name in the dictionary for the record?
            # don't create a list entry for data points unless both x and y are available
            if keyrecord and xname in keyrecord and yname in keyrecord:
                # add the time to the empty row
                dt = datetime2float(parse_date(keyrecord[xname]))
                value = list2float(keyrecord[yname])
                if dt and value and MIN_ORDINAL <= dt <= MAX_ORDINAL: # dates before 1800 don't make sense
                    columns.append([dt,value])
            else:
                warn('The record named '+repr(name)+' of type '+repr(type(keyrecord))+' did not contain x ('+repr(xname)+') or y ('+repr(yname)+') data. Historical data file may be corrupt.')
    if verbose:
        pprint(columns,indent=2)
    return columns

def byrow_key(data, name='mtgox', yname='average', xname='datetime',verbose=False):
    cols = bycol_key(data=data, name=name, yname=yname, xname=xname,verbose=verbose)
    NM = size(cols)
    # don't try to transpose anything that isn't a list of lists
    if (isinstance(NM,(list,tuple)) and len(NM)>1 and NM[0]>0 and NM[0]>0 
                                    and any([n>1 for n in NM]) ): 
        return(transpose_lists(cols))
    else: return cols

def str2float(s=''):
    """Convert value string from a webpage into a float

    Processes commas, units, and magnitude letters (G or B,K or k,M,m)
    >>> str2float('$5.125 M USD')
    5125000.0
    """
    # save the original string for warning message printout and debugging
    try:
        return float(s)
    except:
        pass
    try:
        s0 = str(s)
    except:
        try:
            s0 = unicode(s)
        except:
            raise ValueError('Unable to interpret string '+repr(s)+' as a float')
        warn('Non-ascii object '+repr(s)+' passed to str2float')
    s = s0.strip()
    mag = 1.
    scale = 1.
    # TODO: add more (all Standard International prefixes)
    mags = {'G':1e9,'M':1e6,'k':1e3,'K':1e3,'m':1e-3}
    # factors just for reference not for conversion
    # TODO: pull factors from most recent conversion rate data in historical file or config file?
    # TODO: add national currencies and a few digital ones (e.g. Linden dollars)
    units = {'$':1.,'USD':1.,'AUD':1.3,'BTC':5.,'EU':2.,'bit':1e-3} 
    # TODO: DRY-out
    s=s.strip()
    if s.lower().find('kb')>=0:
        s=s.replace('KB','K').replace('kb','K').replace('Kb','K').replace('kB','K')
    for k,m in mags.items():
        if s.rfind(k) >= 0:
            mag *= m
            s=s.replace(k,'')
    for k,u in units.items():
        s=s.replace(k,'') 
        # scale/units-value unused, TODO: return in a tuple?
        scale *= u
    s=s.strip()
    try:
        return float( s.replace(',','').strip() )*mag
    except:
        warn('Unable to interpret string '+repr(s0)+'->'+repr(s)+' as a number')
    return s # could return None

def list2float(s=''):
    """Convert a multi-dimensional list of strings to a multi-D list of floats

    Processes commas, units, and magnitude letters (G or B,K or k,M,m)
    >>> list2float([['$5.125 M USD','0.123 kB'],[1e-9]])
    [[5125000.0, 123.0], [1e-09]]
    """
    # convert some common iterables into lists
    if isinstance(s,(list,set,tuple)):
        return [list2float(x) for x in s]
    try:
        # maybe one day the float conversion will be 'vectorized'! ;)
        return float(s)
    except:
        if not s:
            return NaN
        if not isinstance(s,(str,unicode)):
            warn("Unable to interpret non-string data "+repr(s)+" which is of type "+str(type(s)))
        # convert bools and NoneTypes to 0. Empty lists have already returned.
        if not s:
            return 0.
        # TODO: check tg.nlp.is_bool() before converting to numerical float
        return str2float(s) 

def datetime2float(dt=None):
    """Convert datetime object to a float, the ordinal number of days since epoch (0001-01-01 00:00:00)

    >>> datetime2float(datetime.datetime(2012,4,20,23,59,59,999999))
    734613.999988426
    """
    if isinstance(dt,(list,set,tuple)):
        if len(dt)==2: # 2-length date vectors are interpreted as the bounds of a daily series
            # min max slice shenanigans is to get this snippet closer to something more general
            dt = [ min( datetime2float(dt[:-1])), 
                   max( datetime2float(dt[-1:])) ] 
            return [ float(x) for x in range(int(min(dt)), int(max(dt))+1) ]
        else:
            return [ datetime2float(x) for x in dt ]
    if isinstance(dt, str):
        return datetime2float(parse_date(dt))
    if isinstance(dt, datetime.datetime):
        return float(dt.toordinal())+dt.hour/24.+dt.minute/24./60.+dt.second/24./3600.
    try:
        return float(dt)
    except:
        return dt or []

def cov(A,B):
    """Covariance of 2 equal-length lists of scalars"""
    ma = mean(A)
    mb = mean(B)
    return sum([(a-ma)*(b-mb) for a,b in zip(A,B)])/len(A)

def pearson(A,B):
    """Pearson correlation coefficient between 2 equal-length lists of scalars"""
    return cov(A,B)/std(A)/std(B)


def lag_correlate(rows, lead=1, verbose=True):
    """
    Correlate 2 data sets, lagging the data in B by N sample periods

    Recursively handles deep dimensionality.
    
    Assumes that A and B contain data in rows (so they are typically wide).

    Even though this example works like I'd hoped indicating that lagged data
    has higher lag_correlation than unlagged (lock-step) data. But this doesn't
    appear to be true generally. So this approach may be misguided.

    Examples:
    >>> lag_correlate([[1,2,3,2,1,2,3,2,1],[1,2,3,2,1,2,3,2,1]],lead=1)
    0.0
    >>> lag_correlate([[1,2,3,2,1,2,3,2,1],[2,3,2,1,2,3,2,1,2]],lead=1)
    0.9999999999999999

    Note:
    for SAMPLE_BIAS_COMP = 1 , second example should give
      0.875 
    instead of 1.0 due to division by N-1 instead of N

    """
    if not isinstance(rows,collections.Iterable): 
        raise ValueError('Cannot calculate the correlation coefficient for a scalar (non-iterable)')
    NM = size(rows)
    # for a 3-D matrix you need a 3-D correlation matrix
    # FIXME:
    if NM[-1]>2 and len(NM)==3 and NM[-2]==2:
        C = [[0. for a in rows] for b in rows[0]]
        for i,AA in enumerate(rows):
            for j,BB in enumerate(rows):
                C[i][j]=lag_correlate([AA[1],BB[1]],lead=lead,verbose=verbose)
        return C
    
    if 2 == len(NM) and 2 == NM[0] and 2 < NM[1]:
        A = rows[0]
        B = rows[1]
    elif 1 == len(NM) and 2 < NM[0]:
        A = rows # autocorolation for a single timeseries (single list, array, vector)
        B = rows
    else:
        raise ValueError('Not sure what do do to calculate the correlation for the rows of a matrix of size '+str(NM))
    L = int(lead)
    if   L>0:
        c = pearson(A[L: ],B[  :-L])
    elif L<0:
        c = pearson(A[ :L],B[-L:  ])
    else:
        c = pearson(A     ,B       )
    if verbose>2:
        print 'Returning a Pearson correlation coefficient in lag_correlate: '+repr(c)
    return c # return a scalar if 2 timeseries were provided

def combo_correlate(A,B):
    """Correlate every row in A with every row in B

    Unlike lag_correlate, which reduces the dimensionality of the data by 1,
    this operation maintains the dimensionality. So 2 matrixes will produce 
    a matrix of correlation coefficients.
    """
    pass

def transpose_lists(lists):
    """Transpose a list of lists

    TODO: fill gaps in inconsistent row lengths with None elements to maintain geometry

    Examples:
    >>> transpose_lists([[1, 2, 3], [4, 5, 6], ])
    [[1, 4], [2, 5], [3, 6]]

    It even works for matrixes with inconsistent row lengths (though it may not do what you intend)
    >>> transpose_lists([[0, 1, 2, 3], [4, 5, 6, 7, 8], [9, 10, 11]])
    [[0, 4, 9], [1, 5, 10], [2, 6, 11], [3, 7], [8]]
    """
    NM = size(lists)
    if not isinstance(NM,(tuple,list)):
        raise ValueError("Can't transpose a scalar!"+str(lists))
        return lists
    N=NM[0]
    M=NM[1]
    if not (NM > 0 and M > 0):
        return lists

    # create empty lists
    result = []
    for n in range(M):
        result.append([])

    # put the rows in the columns
    for n,l in enumerate(lists):
        for m,el in enumerate(l):
            #print n,m,l,el,result
            result[m].append(el)

    return result

def test_read_json(verbose=False):
    #data is a list of dictionaries obtained from the json file
    data = load_json()

    #now creating a keylist
    keylist = []
    for item in data:
        itemkey = item.keys()
        keylist = keylist + itemkey

    #keylist is the list of keys from the list of dictionaries
    if verbose:
        print keylist
        print data
    #run it for a sample key 'mtgox' to get its datetime and average intoa list of list
    listoflist = bycol_key(data, name='mtgox', yname='average')
    #[[734608.0348032408, 4.95759]]
    assert len(listoflist)>10
    for l in listoflist:
        assert len(l)==2
        assert l[0]>73400
        assert l[1]>0.1 and l[1]<25.0

def load_json(filepath=FILEPATH, verbose=-3):
    """Load into memory the historical bitcrawl data from database or flat file
    
    Example to load all data but print to the screen on the first record
    > > load_json('data/bitcrawl_historical_data.json',verbose=1)
    Loading data from ...
    """
    
    display_recs = 1e5
    if not filepath:
        filepath = FILEPATH
    if verbose:  
        try:
            display_recs = int(float(verbose))
        except:
            verbose = True
    if verbose:
        print 'Loading json data from "'+filepath+'"'
    # TODO: this should be try: f=open(): to avoid race condition
    #      alternatively readable should return the opened, readable file object
    with open(filepath) as f:
        if verbose:  
            print 'File exists and is readable: "'+filepath+'"'
        s = f.read()
        if verbose:  
            print 'Read '+str(len(s))+' characters.'
        data = json.loads( s )
        if verbose and isinstance(verbose,(str,unicode)):
            print verbose # verbose must be a message or heading to print it
        if verbose:
            print_data(data, n=display_recs, indent=2, pretty=False)
        return data
    raise IOError('File named '+repr(filepath)+' was not readable.')

# TODO: set default url if not url
def bitfloor_book(bids=None,asks=None,verbose=False):
    rest_dict = rest_json(url='https://api.bitfloor.com/book/L2/1',verbose=verbose) 
    return {'bitfloor':rest_dict}

def extract(s='', prefix=r'', regex=r'', suffix=r''):
    # TODO: extract or create a variable name along with extracting the actual numerical value, see tg.nlp
    # TODO: extract or create a unit of measure string along with extracting the actual numerical value, see tg.nlp
    r = re.compile(r'(?:'+prefix+r')\s*'+r'(?P<quantity>'+regex+r')') # inefficient to compile the regex
    mo = r.search(s)
    if mo:
        return (mo.group(mo.lastindex))
    return None

# TODO: set default url if not url
def mine_data(url='', prefixes=r'', regexes=r'', suffixes=r'', names='', verbose=False):
    if verbose:
        print 'Mining URL "'+url+'" ...'
    if not url: 
        return None
    page=Bot().GET(url)
    dt = datetime.datetime.now(tz=Local)
    dat = {'datetime':str(dt),'url':url}
    if names and isinstance(names,str):
        name = names
    elif isinstance(names,(list,tuple)) and len(names)==1:
        name = names[0]
    else:
        name = 'data'
    if verbose:
        print 'Retrieved '+str(len(page))+' characters/bytes at '+ str(dt)
    if not page:
        return None
    if (  prefixes and regexes and names and isinstance(prefixes,list) and
          isinstance(regexes,list) and isinstance(names,list) and 
          len(regexes)==len(prefixes)==len(names) ):
        for i,prefix in enumerate(prefixes):
            q=extract(s=page,prefix=prefix,regex=regexes[i])
            if q:
                dat[names[i]]=q
    elif (prefixes and regexes and isinstance(prefixes,list) and 
          isinstance(regexes,list) and len(regexes)==len(prefixes) ):
        for i,prefix in enumerate(prefixes):
            q=extract(s=page,prefix=prefix,regex=regexes[i])
            if q:
                dat[name+str(i)]=q
    elif isinstance(prefixes,list) and isinstance(prefixes[0],list):
        if len(prefixes[0])==2:
            for i,[prefix,regex] in enumerate(prefixes):
                q=extract(s=page,prefix=prefix,regex=regex)
                if q:
                    dat[name+str(i)]=q
        elif len(prefixes[0])==3:
            for i,[prefix,regex,suffix] in enumerate(prefixes):
                q=extract(s=page,prefix=prefix,regex=regex,suffix=suffix)
                if q:
                    dat[name+str(i)]=q
# this condition taken care of by earlier setting name=names
#    elif prefixes and regexes and names and isinstance(prefixes,str) and
#            isinstance(regexes,str) and isinstance(names,str):
#        dat[names]=extract(s=page,prefix=prefixes,regex=regexes)
    elif names and prefixes and regexes and isinstance(prefixes,str) and isinstance(regexes,str) and isinstance(names,str):
        dat[names]=extract(s=page,prefix=prefixes,regex=regexes)
    elif page and prefixes and regexes and isinstance(prefixes,str) and isinstance(regexes,str):
        dat['data']=extract(s=page,prefix=prefixes,regex=regexes)
    elif isinstance(prefixes,dict):
        for name,l in prefixes.items():
            if len(l)==2:
                q=extract(s=page,prefix=l[0],regex=l[1])
            elif len(l)==3:
                q=extract(s=page,prefix=l[0],regex=l[1],suffix=l[2])
            else:
                warn('Invalid data mining regular expression dict format')
            if q and name:
                dat[name]=q
            else:
                warn('Unsuccessful mining of "'+str(name)+'" <= "'+str(url)+'" with:\n  '+str(l)+'\n')
                if not q:
                    warn('No numerical data was extracted.')
                if not name:
                    warn('No name for the numerical data was provided.')
    return dat

def are_all_urls(urls):
    if isinstance(urls,dict):
        return all([ k[0:min(4,len(k))]=='http' for k in urls.keys()])
    elif isinstance(urls,(list,tuple)) and isinstance(urls[0],str): 
        return all([ k[0:min(4,len(k))]=='http' for k in urls])
    return False

def join_json(data_list=[],sep=',\n',prefix='[\n\n',suffix='\n]\n'):
    #return ',\n'.join( [ json.dumps(data,indent=2) for data in data_list ] ) + terminator
    json_strings = []
    for data in data_list:
        json_strings.append(json.dumps(data,indent=2))
    return prefix + ( ',\n'.join(json_strings) ) + suffix

def make_tall(lol):
    """Ensures that a list of list has more rows than columns

    >>> make_tall([range(6),[float(x)**1.5 for x in range(6)],range(3,-3,-1)])
    [[0, 0.0, 3], [1, 1.0, 2], [2, 2.8284271247461903, 1], [3, 5.196152422706632, 0], [4, 8.0, -1], [5, 11.180339887498949, -2]]
    """
    N,M = size2(lol)
    #print N,M
    # if it's already a single-dimension array/list/vector then its already "wide"
    # don't convert it to a 2-D matrix
    if M <= 0:
        return lol
    if N<M:
        lol=transpose_lists(lol)
    return lol

def make_wide(lol):
    """Ensures that a list of list has more columns than rows

    TODO:
    Makerecursive so it will work on high-dimensional lists (at least 3D and 4D)

    Examples:
    >>> make_wide([range(6),[float(x)**1.5 for x in range(6)],range(3,-3,-1)])
    [[0, 1, 2, 3, 4, 5], [0.0, 1.0, 2.8284271247461903, 5.196152422706632, 8.0, 11.180339887498949], [3, 2, 1, 0, -1, -2]]
    """
    # TODO size() needs to handle high-dimensionality
    N,M = size2(lol)
    # if it's already a single-dimension array/list/vector then its already "wide"
    # don't convert it to a 2-D matrix
    if M<=0: 
        return lol
    if N>M:
        lol=transpose_lists(lol)
    return lol

def unoffset(data,columns=[0]):
    """Subtracts the first value in the first column of a list from all the elements in that first column

    Designed for use with datetime values that have been converted to an ordinal 
    and thus have large 'day-numbers'
    >>> unoffset([range(75000,75005),[float(x)**1.5 for x in range(5)]])
    [[0, 1, 2, 3, 4], [[0.0, 1.0, 2.8284271247461903, 5.196152422706632, 8.0]]]
    """
    if isinstance(data, list):
        if isinstance(data[0],list):
            N,M = size2(data)
            if N>M:
                d = make_tall([[r[0]-data[0][0] for r in data],make_wide(data)[1:]])
            else:
                d = [[t-data[0][0] for t in data[0]],data[1:]]
        else:
            d = [t-data[0] for t in data]
        return d
    warn('Unable to unoffset data of type '+str(type(data))+'.')
    return None

def mean(lol): 
    """
    Compute mean (expected value, or average) of columns (or rows, if rows longer).

    Recursively handles high-dimensional lists, even if lists in a dim. vary in length 
    as long as all elements have the same dimension (matrix, list, scalar, etc)
    >>> mean([[[2,3,4],[-4,-4,-4],[-8,-3,9,-1]],[[1,2,3],[4,5],[2]]])
    [[3.0, -4.0, -0.75], [2.0, 4.5, 2.0]]
    """
    if isinstance(lol,list):
        if isinstance(lol[0],list):
            #rows = make_wide(lol) # if this could handle high-dimensional lists we'd be in business
            # won't this recursively dive into a multidimensional list?
            return [mean(row) for row in lol] 
        else:
            return float(sum(lol))/len(lol)

def detrend(lol):
    pass

def var(lol): 
    """
    Compute variance of columns of data (or rows, whichever are longer).

    Recursively handles high-dimensional lists, even if lists in a dim. vary in length 
    as long as all elements have the same dimension (matrix, list, scalar, etc)

    Example:   
    >>> var([[[2,3,4],[-4,-4,-4],[-8,-3,9,-1]],[[1,2,3],[4,5],[2]]])
    [[0.6666666666666666, 0.0, 38.1875], [0.6666666666666666, 0.25, 4]]

    Note:
    Example will give 
      [[1.0, 0.0, 50.916666666666664], [1.0, 0.5, 4]]
    if SAMPLE_BIAS_COMP is set to 1 in the contants section bitcrawl.py
    """
    if isinstance(lol,list):
        if isinstance(lol[0],list):
            #rows = make_wide(lol) # if this could handle high-dimensional lists we'd be in business
            # won't this recursively dive into a multidimensional list?
            return [var(row) for row in lol] 
        else:
            if len(lol)>1:
                mu = mean(lol)
                # all sorts of essoteric math reasons for dividing by N-1 instead of N
                return sum([(x-mu)**2 for x in lol])/(len(lol)-SAMPLE_BIAS_COMP)
            else:
                return lol[0]**2
    return lol

# TODO: obviously there's a non-DRY pattern here, 
#       where any function that operates on scalar or vector can be made to operate 
#       on a list of scalars or list of list of scalars, etc
def std(lol): 
    from math import sqrt
    #v = var(lol) # FIXME: doing this with every recursive call is phenommenally inefficient
    if isinstance(lol,list):
        if isinstance(lol[0],list):
            return [std(var(el)) for el in lol] 
        return sqrt(var(lol))
    return sqrt(var(lol))

def columns2xy(columns):
    """
    Creates matrices suitable for matplotlib.pyplot.plot(x,y)

    >>> columns2xy([range(3),[x**1.3 for x in range(3)],[3.*x for x in range(3)]])
    ([[0, 0], [1, 1], [2, 2]], [[0.0, 0.0], [1.0, 3.0], [2.4622888266898326, 6.0]])
    """
    #print 'size',size(columns)
    rows = make_wide(columns)
    #print 'size',size(rows)
    #print 'size2',size2(rows)
    N,M = size2(rows, errors=True, verbose=True)
    if N>1:
        return make_tall([rows[0]]*(N-1)), make_tall(rows[1:])
    elif N==1:
        return make_tall(range(M)), make_tall(rows)
    return None, None

def col_normalize(columns):
    """Normalize each column so that it spans the range 0..1

    Helpful for plotting multiple quantities on the same scale.
    Returns enough information to reconstruct the data or annotate the plot.
    >>> col_normalize([[1,2e5],[2,5e5],[3,4e5]])
    ([[0.0, 0.0], [0.5, 1.0], [1.0, 0.6666666666666666]], [1, 200000.0], [2, 300000.0])
    """
    rows = transpose_lists(columns)
    rows,minr,sf = row_normalize(rows) # return enough data to recover the original
    return transpose_lists(rows), minr, sf

def row_normalize(rows):
    """Normalize each row so that it spans the range 0..1

    Helpful for plotting multiple quantities on the same scale.
    Returns enough information to reconstruct the data or annotate the plot.
    >>> row_normalize([[1,2e5],[2,5e5],[3,4e5]])
    ([[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]], [1, 2, 3], [199999.0, 499998.0, 399997.0])
    """
    sf = []
    minr = []
    for i,r in enumerate(rows):
        maxr = max(r)
        minr.append(min(r))
        sf.append(maxr-minr[i])
        for j,el in enumerate(r):
            rows[i][j] = float(el-minr[i])/sf[i]
    return rows,minr,sf # return enough data to recover the original

def display_correlation(rows, labels, leads=[0,1], verbose=False):
    """Print to terminal a matrix of Pearson correlation coefficients
    
    Assumes rows contain time series (so the 2-D matrix is wider than it is tall)
    First row is time (independent variable)
    Second row is one of the dependent variables
    
    """
    if not rows:
        return
    print 'leads=',leads
    print 'rows=',rows
    leads = leads or [0]
    if isinstance(leads,(float,int)):
        if int(leads)==0:
            leads = [0]
        if leads>0:
            leads = range(min(int(leads)+1, 10))
        elif leads<0:
            leads = range(max(int(leads)-1,-10))
    print '='*60
    print 'Parameters for which correlation matrix was computed (in the order of matrix columns/rows):'
    print '-'*60
    pprint(labels,indent=2)
    print '='*60
    print size(rows)
    NM = size(rows)
    #assert len(NM)==2
    assert NM[-2]==2 # each time series is 2 rows of data [time, value]
    assert NM[-1]>2 # time series must be in rows of the inner dimension
    assert len(NM)==3 # must be 3-D, a list of 2-D time series
    for lead in leads:
        # This is the hard-coded proof-of-concept forecasting algorithm
        print '*'*60
        print 'Pearson correlation coefficient(s) for a lead/lag of '+str(lead)
        print '-'*60
        C = lag_correlate(rows=rows,lead=lead)
        if verbose>2:
            print 'size of correlation matrix: '+repr(size(C))
            print 'correlation matrix (C)=     '+repr(C)
        for c in C:
            print '[' + ', '.join('%+0.2f' % c1 for c1 in c) + ']'
        #TODO calculate for all paramters and find the maximum
        print '*'*60

def plot_data(columns=None, site=['mtgox'], value=['average'], title='Normalized ' +__name__+' Data', quiet=False, normalize=False):
    """Plot 2-D points in first to columns in a list of lists

    Example 
    # doctests will pause and user must close plot for this test to pass
    >>> plot_data([[1,1],[2,4],[3,9]],quiet=True) # displays a plot, then, when you close the plot, prints this
    [[1, 1], [2, 4], [3, 9]]
    """
    site = [site] if isinstance(site,str) else site
    value = [value] if isinstance(value,str) else value
    legends = [str(s)+':'+str(v) for s,v in zip(site,value)]
    legends = [s[max(len(s)-14,0):] for s in legends]

    if not isinstance(site,list) or not isinstance(value,list) or not isinstance(site[0],str) or not isinstance(value[0],str):
        warn('Unable to identify the values that you want to plot. '+
            ' \n site = '+ str(site)+
            ' \n value = '+ str(value)+
            ' \n type(columns) = '+str(type(columns))+
            ' \n size(columns) = '+str(size(columns))+'\n' )
        return None

    data=None
    # TODO: load data inside one set of conditionals, then extrace columns in another set of conditionals
    if not columns:
        data = load_json(verbose=False)
        columns = byrow_key(data,name=site[0],yname=value[0],xname='datetime')
    if isinstance(columns, str):
        data = load_json(filepath=columns,verbose=False)
        columns = byrow_key(data,name=site[0],yname=value[0],xname='datetime')
    if not (isinstance(columns,list) and isinstance(columns[0],list)):
        warn('Unable to plot data of type '+str(type(columns)))
        return None

    i=1
    # only need to interpolate if more than one column is being plotted
    if data and i<len(site) and columns:
        t = columns[0]
        while i<len(site):
            s,v = site[i],value[i]
            cols2 = byrow_key(data,name=s,yname=v,xname='datetime')
            # interpolate the new data to line up in time with the original data
            columns.append(interpolate(cols2[0],cols2[1],t))
            i += 1

    x,y = columns2xy(columns)

    if normalize==True:
        y,miny,sfy = col_normalize(y)
    plt.plot(x,y)
    plt.title(title)
    plt.legend(legends)
    plt.grid('on')
    if not quiet:
        print 'A plot titled "'+title+'" was displayed. Close it to procede.'
        plt.show()
    return columns

# TODO: refactor as class method bitcrawl.Data.dump() or Django Model with at repr or str or dump() method
def print_data(data, n=-3, indent=2, pretty=True):
    """Print the data strcture in an indented outline form
    
    *n* = number of records to print (from the end if <0, from the beginning if >0)
    """
    n = int(n) 
    if not n:
        return
    if pretty:
        pprint(   data[min(0,n):min(len(data),abs(n))], indent=indent)
    else:
        print json.dumps(data[min(0,n):min(len(data),abs(n))], indent=indent)

def test(verbose=True, internet=False):
    import doctest 
    optionflags=doctest.ELLIPSIS

    print dir()
    if internet:
        doctest.testmod( verbose = verbose , optionflags=optionflags )
        doctest.testfile( 'docs/bitcrawl.rst', verbose = verbose, optionflags=optionflags)
    else:
        m = sys.modules.get('__main__')
        print m
        print m.__dict__
        # print dir(m)
        for tf in dir(m):
            print tf
            print len(dir(tf))
            #run_docstring_examples(tf,globs=None)

if __name__ == "__main__":
    import sys
    internet = False
    verbose = True
    # todo, don't check argv[0]
    for a in sys.argv:
        if a.startswith('-I') or a.startswith('--I'):
            internet == False
        if a.startswith('-i') or a.startswith('--i'):
            internet == True
        al = a.lower()
        if al.startswith('-q') or al.startswith('--q'):
            verbose == False
        if al.startswith('-v') or al.startswith('--v'):
            verbose == True
    # TODO: don't rull all tests!
    test(verbose=verbose, internet=internet)

