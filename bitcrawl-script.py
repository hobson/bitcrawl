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

	FIXME:
	
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

	::Author: Hobson Lane, Alex Gagnon, and Nataraj
	::License: CC BY-NC-SA
	::Attribution: Based Udacity.com code licensed under CC BY-NC-SA
"""

import bitcrawl as bc
from argparse import ArgumentParser
from warnings import warn

def parse_args():
	"""Parse the command line arguments

		TODO:
			allow user to input a number format and prefix in some form other than python regexes
			add options or dictionary members to hold patterns for "unit-of-measure" and "suffix"
			generalize the format to allow user to ask the miner to count links at the url, rather than just extracting a literal value
	"""

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
		default = bc.URLs,
		help    = 'URL to mine data from or list of dictionaries of dictionaries defining regular expressions and URLs to extract data.',
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
				d[u]=bc.mine_data(url=u, prefixes=r, verbose=not o.quiet)
		# otherwise assume the new format where each dict key is a name, and 'url' is a key of the nested dict
		else:
			for name,r in o.urls.items():
				d[name]=bc.mine_data(url=r.pop('url'), prefixes=r, verbose=not o.quiet)
	else:
		raise ValueError('Invalid URL, prefix, or regex argument.')
	
	data=[ d,
		   bc.bitfloor_book       (            verbose=not o.quiet),
		   bc.wikipedia_view_rates(            verbose=not o.quiet),
		   bc.get_links           (max_depth=0,verbose=not o.quiet)
		 ]

	# compose a json string that can be appended to the end of a list within a json file (prefix = '')
	json_string = join_json(data,prefix='',suffix='\n]\n') 

	# TODO: make writable() check for a regex match (for formating and content verificaiton)
	# TODO: make writable() write the file with acceptable initial content
	if not bc.updateable(o.path,initial_content='[\n\n]\n'): 
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

