#!/usr/bin/python
"""Crawls the web looking for quantitative information about bitcoin popularity.

	Examples (require Internet connection):
	>>> bitcrawl
	Mining URL "https://en.bitcoin.it/wiki/Real_world_shops" ...
	Retrieved 28835 characters/bytes at 2012-04-02 17:37:06.709302+08:00
	Mining URL "https://mtgox.com" ...
	Retrieved 22493 characters/bytes at 2012-04-02 17:37:07.840549+08:00
	Mining URL "http://bitcoincharts.com/about/markets-api/" ...
	Retrieved 7712 characters/bytes at 2012-04-02 17:37:14.518451+08:00
	Mining URL "https://en.bitcoin.it/wiki/Main_Page" ...
	Retrieved 24069 characters/bytes at 2012-04-02 17:37:16.770427+08:00
	Mining URL "https://bitcoinconsultancy.com/wiki/Main_Page" ...
	Retrieved 18188 characters/bytes at 2012-04-02 17:37:19.173755+08:00
	Mining URL "https://en.bitcoin.it/wiki/Trade" ...
	Retrieved 303426 characters/bytes at 2012-04-02 17:37:22.602371+08:00
	Getting REST data from URL "https://api.bitfloor.com/book/L2/1" ...
	Retrieved a 1004-character JSON string at 2012-04-02 17:37:24.520884+08:00
	Checking wikipedia view rate for "Bitcoin"
	Mining URL "http://stats.grok.se/en/latest/Bitcoin" ...
	Retrieved 11745 characters/bytes at 2012-04-02 17:37:28.240635+08:00
	Checking wikipedia view rate for "James_Surowiecki"
	Mining URL "http://stats.grok.se/en/latest/James_Surowiecki" ...
	Retrieved 11746 characters/bytes at 2012-04-02 17:37:29.574902+08:00
	Counting links by crawling URL "https://en.bitcoin.it/wiki/Trade" to a depth of 0...
	Retrieved 225 links at "https://en.bitcoin.it/wiki/Trade"
	Appended json records to "/home/hobs/Notes/notes_repo/bitcoin trend data.json"
	MtGox price is $4.79240
	
	Standard Module Dependencies:
		argparse	ArgumentParser
		urllib  	urlencode, urlopen,...
		urllib2 	HTTPRedirectHandler, HTTPCookieProcessor, ...
		time    	sleep
		datetime	now()
		httplib 	IncompleteRead
	Nonstandard Module Dependencies:
		tz      	Local

	LOG: (imperfectly duplicates git log)
	+ 2012/04/11 HL Nat improved README based on his platform setup experience with git, bitbucket, and python for Windows
	+ 2012/04/11 HL FIXED bitfloor order book REST data retrieval using api.bitfloor
	+ 2012/04/12 HL added load_json for Alex so he can focus on statistics calculations on the dict of data
	+ 2012/04/12 HL removed and rewrote the historical_data.json file to be valid because json file had None for some elements in list due to data extraction (regex) bugs
	
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

	Author: Hobson Lane dba TotalGood
	License: GPL v3
	Attribution: Based on code at udacity.com licensed to CC BY-NC-SA
"""

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

FILENAME=os.path.expanduser('~/bitcrawl_historical_data.json') # change this to a path you'd like to use to store data

def parse_args():
	"""Parse the command line arguments

		TODO:
			allow user to input a number format and prefix in some form other than python regexes
			add options or dictionary members to hold patterns for "unit-of-measure" and "suffix"
			generalize the format to allow user to ask the miner to count links at the url, rather than just extracting a literal value
	"""

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
	p = ArgumentParser(description=__doc__.strip())
	p.add_argument(
		'-b','--bitfloor','--bf',
		type    = int,
		nargs   = '?',
		default = 0,
		help    = 'Retrieve N prices from the order book at bitfloor.',
		)
	p.add_argument(
		'-u','--urls','--url',
		type    = str,
		nargs   = '*',
		default = URLs,
		help    = 'URL to mine data from.',
		)
	p.add_argument(
		'-p','--prefix',
		type    = str,
		nargs   = '*',
		default = '', 
		help    = 'HTML that preceeds the desired numerical text.',
		)
	p.add_argument(
		'-r','--regex','--regexp','--re',
		type    = str,
		nargs   = '*',
		default = '',
		help    = 'Python/Perl regular expression to capture numerical string only.',
		)
	p.add_argument(
		'-v','--verbose',
		action  = 'store_true',
		default = False,
		help    = 'Print out (to stdout) progress messages.',
		)
	p.add_argument(
		'-q','--quiet',
		action  = 'store_true',
		default = False,
		help    = "Don't output anything to stdout, not even the numerical values minded. Overrides verbose setting.",
		)
	p.add_argument(
		'-t','--tab',
		action  = 'store_true',
		default = 'false',
		help    = "In the output file, precede numerical data with a tab (column separator).",
		)
	p.add_argument(
		'-n','--newline',
		action  = 'store_true',
		default = 'false',
		help    = "In the output file, after outputing the numerical value, output a newline.",
		)
	p.add_argument(
		'-s','--separator','-c','--column-separator',
		metavar = 'SEP',
		type    = str,
		default = '',
		help    = "In the output file, precede numberical data with the indicated string as a column separator.",
		)
	p.add_argument(
		'-m','--max','--max-results',
		metavar = 'N',
		type=int,
		default = 1,
		help    = 'Limit the maximum number of results.',
		)
	p.add_argument(
		'-f','--path','--filename',
		type    = str,
		#nargs  = '*', # other options '*','+', 2
		default = FILENAME,
		help    = 'File to append the numerical data to (after converting to a string).',
		)
	return p.parse_args()

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

#!/usr/bin/env python



class Bot:
	"""A browser session that follows redirects and maintains cookies.
	
	TODO: 
		allow specification of USER_AGENT, COOKIE_FILE, REFERRER_PAGE
		if possible should use the get_page() code from the CS101 examples to show "relevance" for the contest
	"""
	
	# don't wait less than 0.1 s or longer than 1 hr when retrying a network connection
	
	def __init__(self):
		self.response    = ''
		self.params      = ''
		self.url         = ''
		redirecter  = urllib2.HTTPRedirectHandler()
		cookies     = urllib2.HTTPCookieProcessor()
		self.opener = urllib2.build_opener(redirecter, cookies)
	def GET(self, url,max_retries=10,retry_delay=3):
		retry_delay = min(max(retry_delay,0.1),3600)
		datastr = '' # not necessary?
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
	try:
		return urllib.urlopen(url).read()
	except:
		return ''

def get_next_target(page):
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
		f = open(o.path,'r')
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

def load_json(filename=FILENAME,verbose=False):
	if verbose:
		print 'Loading json data from "'+filename+'"'
	if readable(filename):
		f = open(filename,'r')
		s = f.read()
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

if __name__ == "__main__":
	o = parse_args()
	
	if not o.quiet or o.verbose:
		load_json(filename=o.path,verbose='Historical data already mined:') # verbose means the data will print out with that as the heading

	# mine raw urls
	d = dict()

	if type(o.urls)==dict:
		# TODO: this check and "iterification" of mine_data() should happen inside the function
		# check to see if all the dictionary keys look like urls
		if are_all_urls(o.urls):
			for u,r in o.urls.items():
				d[u]=mine_data(url=u, prefixes=r, verbose=not o.quiet)
		# otherwise assume the new format where each dict key is a name, and 'url' is a key of the nested dict
		else:
			for name,r in o.urls.items():
				d[name]=mine_data(url=r.pop('url'), prefixes=r, verbose=not o.quiet)
	else:
		raise ValueError('Invalid URL, prefix, or regex argument.')
	
	data=[ d,
		   bitfloor_book       (            verbose=not o.quiet),
		   wikipedia_view_rates(            verbose=not o.quiet),
		   get_links           (max_depth=0,verbose=not o.quiet)
		 ]

	# compose a json string that can be appended to the end of a list within a json file (prefix = '')
	json_string = join_json(data,prefix='',suffix='\n]\n') 

	# TODO: make writable() check for a regex match (for formating and content verificaiton)
	# TODO: make writable() write the file with acceptable initial content
	if not updateable(o.path,initial_content='[\n\n]\n'): 
		print 'ERROR! Unable to log data to "'+o.path+'". Printing to stdout instead...'
		print json_string 
		raise RuntimeError('Unable to log data to "'+o.path+'".')

	# see http://stackoverflow.com/a/1466036/623735 for definitions of file modes (write, read, update)
	#     + = update
	#    a+ = only allow you to seek and write after the end of the existing data 
	#    w+ = truncate (delete existing data) before opening and updating/writing with new data
	#    r+ = leaves existing contents in tact and allows writing, reading, seeking anywhere (random access)
	with open(o.path,'r+') as f: 
		# pointer should be at the end already due to append mode, but it's not,
		f.seek(0,2)  # go to position 0 relative to 2=EOF (1=current, 0=begin), not sure if this is required before the -3 seek
		f.seek(-3,2) # if you do this before seek(0,2) on a "a+" or "w+" file you get "[Errno 22] Invalid argument"
		if f.tell()>10: # file isn't empty
			f.write(',\n') # to allow continuation of the json array/list by overwriting the ']' that terminates the existing list
		else:
			f.write('\n') # to allow continuation of the json array/list by overwriting the ']' that terminates the existing list
		f.write(json_string)
		if not o.quiet:
			print 'Appended json records to "'+o.path+'"'
			try:
				print 'MtGox price is '+str(data[0]['mtgox']['average'])
			except KeyError:
				print 'Unable to retrieve the MtGox price. Network dropout? Format change at MtGox?'

	if o.verbose:
		'New data extracted from web pages...'
		print json_string

