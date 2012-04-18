#!/usr/bin/python
"""Module for crawling the web, extracting numbers, counting links and other stats

	Calculates statistics of the data gathered and plots 2-D plots.
	
	Standard Module Dependencies:
		argparse	ArgumentParser
		urllib  	urlencode, urlopen,...
		urllib2 	HTTPRedirectHandler, HTTPCookieProcessor, etc
		time    	sleep
		datetime	now(), datetime.strptime(), datetime.datetime(), etc
		httplib 	IncompleteRead
		numpy   	
		matplotlib	pyplot.plot

	Nonstandard Module Dependencies:
		tz      	Local # local time zone object definition

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
import pprint
from argparse import ArgumentParser
import re
from warnings import warn
import numpy as np
import matplotlib.pyplot as plt

FILENAME=os.path.expanduser('data/bitcrawl_historical_data.json') # change this to a path you'd like to use to store data

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
	'consultancy': {
		'url': 'https://bitcoinconsultancy.com/wiki/Main_Page',
		'visits':
			[r'has\sbeen\saccessed\s',
			 r'([0-9]{1,3}[,]?){1,4}'  ] }, 
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
	"""
	
	def __init__(self):
		self.response    = ''
		self.params      = ''
		self.url         = ''
		redirecter  = urllib2.HTTPRedirectHandler()
		cookies     = urllib2.HTTPCookieProcessor()
		self.opener = urllib2.build_opener(redirecter, cookies)
	def GET(self, url,max_retries=10,retry_delay=3):
		# don't wait less than 0.1 s or longer than 1 hr when retrying a network connection
		retry_delay = min(max(retry_delay,0.1),3600)
		datastr = '' # unnecessary?
		try:
			file_object = self.opener.open(url)
		# build_opener object doesn't handle 404 errors, etc !!! 
		except httplib.IncompleteRead, e:
			print "HTTP read for URL '"+url+"' was incomplete: %d" % e.code
		except urllib2.HTTPError, e:
			print "HTTP error for URL '"+url+"': %d" % e.code
		except urllib2.URLError, e:
			print "Network error for URL '"+url+"': %s" % e.reason.args[1]
			# retry
			if max_retries:
				print "Waiting "+str(retry_delay)+" seconds before retrying network connection for URL '"+url+"'..."
				print "Retries left = "+str(max_retries)
				time.sleep(retry_delay)
				print "Retrying network connection for URL '"+url+"'."
				return self.GET(url,max_retries-1)
			else:
				print "Exceeded maximum number of Network error retries."
		try:
			datastr = file_object.read() # should populate datastr with an empty string if the file_object is invalid, right?
		except:
			datastr = ''
		return datastr
	def POST(self, url, params):
		self.url    = url
		self.params = urllib.urlencode(parameters)
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
	MONTH                = r'[01]\d',   # 01-12
	DAY         = r'[0-2]\d|3[01]',     # 01-31
	HOUR        = r'[0-1]\d|2[0-4]',    # 01-24
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
		(?P<m>%(MINUTE)s)%(TIME_SEP)s
		(?P<s>%(SECOND)s) 
""" % QUANT_PATTERNS, re.X)

DATETIME_PATTERN = re.compile(r'(?P<date>'+DATE_PATTERN.pattern+r')(?:%(DATE_SEP)s)?(?P<time>'+TIME_PATTERN.pattern+r')' % QUANT_PATTERNS, re.X)

def parse_date(s):
	"""Uses complicated nested regular expressions to proces date-time strings and doesn't work!
	
	# Fails!
	# >>> print parse_date('2012-04-20 23:59:00')
	# (2012, 4, 20, 23, 59, 0)
	"""
	from datetime import datetime
	from math import floor
	
	mo=DATETIME_PATTERN.match(s)
	if mo:
		y = zero_if_none(mo.group('y'))
		if len(y) == 2:
			if y[0] == '0':
				y = int(y) + 2000
#			else:
#				y = int(y)
#				if y > 20 and y < 100:
#					y = y + 1900
		y = int(y)
		mon = int(zero_if_none(mo.group('mon')))
		d = int(zero_if_none(mo.group('d')))
		h = int(zero_if_none(mo.group('h')))
		m = int(zero_if_none(mo.group('m')))
		s_f = float(zero_if_none(mo.group('s')))
		s = int(floor(s_f))
		us = int((s_f-s)*1000000.0)
		return datetime(y,mon,d,h,m,s,us)
	else:
		raise ValueError("Date time string not recognizeable or not within a valid date range (2199 BC to 2199 AD): %s" % s)

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
		# this name needs to reflext the URL specified as an input rather than a hard-coded name
		if verbose:
			print data
		return data
	return None

def readable(path):
	try:
		f = open(path,'r')
		# return f # but this makes readable() just like an f = open(... wrapped in a try
		f.close()
		return True
	except:
		return False

def updateable(path,initial_content='',min_size=0):
	if initial_content:
		min_size = max(min_size,len(initial_content))
	#TODO: use os.path_exists instead of try
	if not min_size:
		try:
			f = open(o.path,'r+') # w = create the file if it doesn't already exist, truncate to zero length if it does
		except:
			return False
		f.close()
		return True
	else:
		if readable(path): # don't open for writing because that will create and truncate it
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
					f = open(o.path,'w')
					f.write(initial_content)
					f.close()
					return True
		else:
			try:
				f = open(path,'w')
			except:
				return False
			if initial_content:
				f = open(o.path,'w')
				f.write(initial_content)
			f.close()
			return True
		return False

def bycol_key(data, name='mtgox', y='average', x='datetime'):#function for returning values given a key of the dictionary data
    columns =[]
    # loops thru each data item in the list
    for record in data:
        # if this record (dict) contains the named key ('mtgox')
        if name in record.keys():
            keyrecord = record[name]
            print 'keyrecord=',keyrecord
            columns.append([])# add an empty row
            # is the requested x data name in the dictionary for the record?
            if x in keyrecord:
            	# add the time to the empty row
            	# leave it as a string and I'll convert to a value
                dt = datetime.datetime.strptime(keyrecord[x][0:-6],"%Y-%m-%d %H:%M:%S.%f")
                dt_value = float(dt.toordinal())+dt.hour/24.+dt.minute/24./60.+dt.second/24./3600.
                columns[-1].append(dt_value)
            if y in keyrecord.keys():
                # float() won't work if there's a dollar sign in the value/price, so get rid of it
                value = float(keyrecord[y].strip().strip('$').strip())
                # add the value to the last row
                columns[-1].append(value)
        #pprint.pprint(columns,indent=2)
    return columns

def transpose_lists(lists):
	"""Transpose a list of lists
	
	>>> print transpose_lists([[1, 2, 3], [4, 5, 6]])
	[[1, 4], [2, 5], [3, 6]]
	"""
	
	N,M = len(lists),len(lists[0])
	
	# create empty lists
	result = []
	for n in range(M):
		result.append([])
	
	# put the rows in the columns
	for n,l in enumerate(lists):
		for m,el in enumerate(l):
			result[m].append(el)
	
	return result
		
def byrow_key(data, key='mtgox', x='datetime', y='average'):#function for returning values given a key of the dictionary data
	cols = bycol_key(data, key, x, y)
	rows=transpose_lists(cols)
	return columns


def test_read_json():
	import json
	from pprint import pprint
	import datetime

	#data is a list of dictionaries obtained from the json file
	data = load_json()

	#now creating a keylist
	keylist = []
	for item in data:
		itemkey = item.keys()
		keylist = keylist + itemkey

	#keylist is the list of keys from the list of dictionaries
	print keylist
	
	print data
	#run it for a sample key 'mtgox' to get its datetime and average intoa list of list
	listoflist = bycol_key(data, key='mtgox', y='average')
	#[[734608.0348032408, 4.95759]]
	assert len(listoflist)>10
	for l in listoflist:
		assert l[0]>73400
		assert l[1]>0.1 and l[2]<25.0
		assert len(l)==2

def load_json(filename=FILENAME,verbose=False):
	if verbose:  print 'Loading json data from "'+filename+'"'
	if readable(filename):
		if verbose:  print 'File exists and is readable: "'+filename+'"'
		f = open(filename,'r')
		s = f.read()
		if verbose:  print 'Read '+str(len(s))+' characters.'
		data = json.loads( s )
		if verbose and isinstance(verbose,str):
			print verbose
		if verbose:
			pprint.pprint(data)
		return data
	return None

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
#	elif prefixes and regexes and names and isinstance(prefixes,str) and
#			isinstance(regexes,str) and isinstance(names,str):
#		dat[names]=extract(s=page,prefix=prefixes,regex=regexes)
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

def plot_data(columns=None):
	"""Plot 2-D points in first to columns in a list of lists
	
	>>> plot_data([[1,1],[2,4],[3,9]])
	[[1, 2, 3], [1, 4, 9]] 
	"""
	if not columns:
		#columns = bycol_key(load_json(),'mtgox','datetime','average')
		columns = bycol_key(load_json())
	elif isinstance(columns, str):
		columns = bycol_key(load_json(path=columns))
	print columns
	rows = transpose_lists(columns)
	print rows
	plt.plot(rows[0],rows[1])
	plt.show()
	#if result[0:11] == str('[<matplotlib.lines.Line2D at 0xb01a66c>]')[0:11]:
	#	return rows,result,result2
	return rows
	return None

# plt.plot('yourdata') plots your data, plt.show() displays the figure.
# Json data needs to be transposed.
# plt.xlabel('some text') = adds label on x axis
# plt.ylabel('some text') = adds label on y axis
# plt.title('Title') = adds title

if __name__ == "__main__":
	import doctest
	doctest.testmod(verbose=True)
