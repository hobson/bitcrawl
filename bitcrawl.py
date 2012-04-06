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
	
	Dependencies:
		argparse -- ArgumentParser
		urllib
		urllib2

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

FILENAME='/home/hobs/Notes/notes_repo/bitcoin trend data.json'

def parse_args():
	# TODO: "meta-ize" this by only requiring number format specification in some common format 
	#       like sprintf or the string input functions of C or python, and then convert to a good regex
	# TODO: add optional units-of-measure and suffix patterns
	# TODO: come up with some generalized format that allows you to count links or other stats on a page rather than just extracting a literal value

	URLs={'network': 
			{ 
			  'url': 'http://bitcoincharts.com/about/markets-api/',
			  'blocks':
				[r'<td class="label">Blocks</td><td>',          # (?<= ... )\s*
				 r'[0-9]{1,9}'                               ],  # (...)
			  'total_btc': # total money supply of BTC
				[r'<td class="label">Total BTC</td><td>',
				 r'[0-9]{0,2}[.][0-9]{1,4}[MmKkGgBb]' ], 
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
				 r'([0-9],)?[0-9]{3},[0-9]{3}'  ] }, 
		'shop': {
			'url': 'https://en.bitcoin.it/wiki/Real_world_shops',
			'visits':
				[r'has\sbeen\saccessed\s',
				 r'([0-9],)?[0-9]{3},[0-9]{3}'  ] }, 
		'bitcoin': {
			'url': 'https://en.bitcoin.it/wiki/Main_Page',
			'visits':
				[r'has\sbeen\saccessed\s',
				 r'([0-9],)?[0-9]{3},[0-9]{3}'  ] }, 
		'consultancy': {
			'url': 'https://bitcoinconsultancy.com/wiki/Main_Page',
			'visits':
				[r'has\sbeen\saccessed\s',
				 r'([0-9],)?[0-9]{3},[0-9]{3}'  ] }, 
		'mtgox':    {
			'url': 'https://mtgox.com',
			'average':
			[r'Weighted Avg:<span>',
			 r'\$[0-9]{1,2}[.][0-9]{3,6}' ],  
			'last':
			[r'Last price:<span>',
			 r'\$[0-9]{1,2}[.][0-9]{3,6}' ],
			'high':
			[r'High:<span>',
			 r'\$[0-9]{1,2}[.][0-9]{3,6}' ],
			'low':
			[r'Low:<span>',
			 r'\$[0-9]{1,2}[.][0-9]{3,6}' ],
			'volume':
			[r'Volume:<span>',
			 r'\$[0-9]{1,9}' ] },
		}
	from argparse import ArgumentParser
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
		help    = 'URL to scape data from.',
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
		help    = 'Output an progress information.',
		)
	p.add_argument(
		'-q','--quiet',
		action  = 'store_true',
		default = False,
		help    = "Don't output anything to stdout, not even the numerical value scraped from the page. Overrides verbose.",
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

#Historic Trade Data
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

COOKIEFILE='/home/hobs/tmp/wget_cookies.txt'
#REFERRERURL='http://google.com'
#USERAGENT='Mozilla'

#!/usr/bin/env python

import urllib
import urllib2

class Bot:
	"""A browser session that follows redirects and maintains cookies."""
	def __init__(self):
		self.response    = ''
		self.params      = ''
		self.url         = ''
		redirecter  = urllib2.HTTPRedirectHandler()
		cookies     = urllib2.HTTPCookieProcessor()
		self.opener = urllib2.build_opener(redirecter, cookies)
#		build_opener creates an object that already handles 404 errors, etc, right?
#			except urllib2.HTTPError, e:
#				print "HTTP error: %d" % e.code
#			except urllib2.URLError, e:
#				print "Network error: %s" % e.reason.args[1]
	def GET(self, url):
		self.response = self.opener.open(url).read()
		return self.response
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
		             regexes=r'[0-9]{1,10}',
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

# TODO: set default url if not url
# TODO: tries to browse to weird URLs and bookmarks, e.g. "href=#Printing"
# TODO: need to count stats like how many are local and how many unique second and top level domain names there are
def get_links(url='https://en.bitcoin.it/wiki/Trade',max_depth=1,max_breadth=1e6,max_links=1e6,verbose=False,name=''):
	import datetime
	from tz import Local
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
	import json, datetime
	from tz import Local
	if verbose:
		print 'Getting REST data from URL "'+url+'" ...'
	data_str = Bot().GET(url)
	dt = datetime.datetime.now(tz=Local)
	if verbose:
		print 'Retrieved a '+str(len(data_str))+'-character JSON string at '+ str(dt)
	dat     = json.loads( data_str )
	dat['datetime']=str(dt)
	dat['url']=url
	return {'bitfloor_book':dat}

# TODO: set default url if not url
def bitfloor_book(url='https://api.bitfloor.com/book/L2/1',bids=None,asks=None,verbose=False):
	return rest_json(url=url,verbose=verbose) 

def extract(s='', prefix=r'', regex=r'', suffix=r''):
	# TODO: extract or create a variable name along with extracting the actual numerical value, see tg.nlp
	# TODO: extract or create a unit of measure string along with extracting the actual numerical value, see tg.nlp
	import re
	r = re.compile(r'(?:'+prefix+r')\s*'+r'(?P<quantity>'+regex+r')') # inefficient to compile the regex
	mo = r.search(s)
	if mo:
		return (mo.group(mo.lastindex))
	return None

# TODO: set default url if not url
def mine_data(url='', prefixes=r'', regexes=r'', suffixes=r'', names='', verbose=False):
	import datetime
	from tz import Local
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
	elif isinstance(prefixes,list) and isinstance(prefixes[0],list) and len(prefixes[0])==2:
		for i,[prefix,regex] in enumerate(prefixes):
			q=extract(s=page,prefix=prefix,regex=regex)
			if q:
				dat[name+str(i)]=q
	elif isinstance(prefixes,list) and isinstance(prefixes[0],list) and len(prefixes[0])==3:
		for i,[prefix,regex,name] in enumerate(prefixes):
			q=extract(s=page,prefix=prefix,regex=regex)
			if q:
				dat[name]=q
# this condition taken care of by earlier setting name=names
#	elif prefixes and regexes and names and isinstance(prefixes,str) and
#			isinstance(regexes,str) and isinstance(names,str):
#		dat[names]=extract(s=page,prefix=prefixes,regex=regexes)
	elif prefixes and regexes and isinstance(prefixes,str) and isinstance(regexes,str):
		dat[name]=extract(s=page,prefix=prefixes,regex=regexes)
	elif isinstance(prefixes,dict):
		for name,[prefix,regex] in prefixes.items():
			q=extract(s=page,prefix=prefix,regex=regex)
			if q:
				dat[name]=q
	return dat

def are_all_urls(urls):
	if isinstance(urls,dict):
		return all([ k[0:min(4,len(k))]=='http' for k in urls.keys()])
	elif isinstance(urls,(list,tuple)) and isinstance(urls[0],str): 
		return all([ k[0:min(4,len(k))]=='http' for k in urls])
	return False

if __name__ == "__main__":
	o = parse_args()
	
	# mine raw urls
	dat = dict()
	if type(o.urls)==dict:
		if are_all_urls(o.urls):
			for u,r in o.urls.items():
				dat[u]=mine_data(url=u, prefixes=r, verbose=not o.quiet)
		else:
			for name,r in o.urls.items():
				dat[name]=mine_data(url=r.pop('url'), prefixes=r, verbose=not o.quiet)
	else:
		raise ValueError('Invalid URL, prefix, or regex argument.')
	
	if o.verbose:
		import pprint
		pprint.pprint(dat)
	
	# get bitfloor book data
	bfdat = bitfloor_book(verbose=not o.quiet)
	if o.verbose:
		pprint.pprint(bfdat)

	# get wikipedia page visit rates
	wikidat = wikipedia_view_rates(verbose=not o.quiet)
	if o.verbose:
		pprint.pprint(wikidat)

	# count links at bitcoin.it/Trade (need a better way of counting the businesses that accept bitcoin)
	links = get_links(max_depth=0,verbose=not o.quiet)
	
	with open(o.path,'r+') as f: # 'a+' and 'w+' don't work
		# pointer should be at the end already due to append mode, but it's not,
		f.seek(0,2)  # go to position 0 relative to 2=EOF (1=current, 0=begin)
		if f.tell()>3:
			f.seek(-3,2) # if you do this before seek(0,2) on a "a+" or "w+" file you get "[Errno 22] Invalid argument"
			#terms=f.read()
			#if terms=='\n]\n':
			#f.seek(-3,2)
			f.write(",\n") # to allow continuation of the json array/list
		else:
			f.write('[\n')  # start a new json array/list
		import json
		f.write(json.dumps(dat,indent=2))
		f.write(",\n") # delimit records/object-instances within an array with commas
		f.write(json.dumps(bfdat,indent=2))
		f.write(",\n") # delimit records/object-instances within an array with commas
		f.write(json.dumps(wikidat,indent=2))
		f.write(",\n") # delimit records/object-instances within an array with commas
		f.write(json.dumps(links,indent=2))
		f.write("\n]\n") #  terminate array brackets and add an empty line
		if not o.quiet:
			print 'Appended json records to "'+o.path+'"'
			print 'MtGox price is '+str(dat['mtgox']['average'])

