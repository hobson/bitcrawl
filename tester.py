#!/usr/bin/env python

from bitcrawl import load_json
def test_load():
	import datetime
	"""Load the historical data json file: list(dict(dict()))
	
	Convert to list(list()), print, and return
	"""
	data=load_json(filename='data/bitcrawl_historical_data.json',verbose=False)
	if not data: return data
	
	columns=[]
	for record in data:
		if 'mtgox' in record.keys():
			mtgox = record['mtgox']
			columns.append([]) #add an empty row
			if 'datetime' in mtgox.keys():
				# add the time to the empty row
				# leave it as a string and I'll convert to a value
				dt = datetime.datetime.strptime(mtgox['datetime'][0:-6],"%Y-%m-%d %H:%M:%S.%f")
				dt_value = float(dt.toordinal())+dt.hour/24.+dt.minute/24./60.+dt.second/24./3600.
				columns[-1].append(dt_value)
			if 'average' in mtgox.keys():
				# float() won't work if there's a dollar sign in the price
				value = float(mtgox['average'].strip().strip('$').strip())
				# add the value to the last row
				columns[-1].append(value)
	import pprint
	pprint.pprint(columns,indent=2)
	return columns

def test_plot():
	columns = test_load()
	plot_data(columns)

def plot_data(columns= [ [] ] ):
	pass

columns = test_plot()

def test_regex():
	f=open('data/pages/virwox.html')
	s=f.read()
	import re
	r=re.compile(r"<tr.*?>USD/SLL</th.*?><td.*?'buy'.*?>[0-9]{1,6}[.]?[0-9]{0,3}")
	mo = r.search(s)
	print s[mo.span()[0]:mo.span()[1]]

	r=re.compile(r"(?s)<fieldset>\s*<legend>\s*Trading\s*Volume\s*\(SLL\)\s*</legend>\s*<table.*?>\s*<tr.*?>\s*<td>\s*<b>\s*24\s*[Hh]ours\s*[:]?\s*</b>\s*</td>\s*<td>")
	mo = r.search(s)
	print s[mo.span()[0]:mo.span()[1]]

	f=open('data/pages/consultancy.html')
	s=f.read()
	r=re.compile(r'has\sbeen\saccessed\s([0-9]{1,3}[,]?){1,4}')
	mo = r.search(s)
	print s[mo.span()[0]:mo.span()[1]]


	f=open('data/pages/mtgox.html')
	s=f.read()
	r=re.compile(r'Volume\s*:\s*<span>\s*'+r'[0-9]{1,9}')
	mo = r.search(s)
	print s[mo.span()[0]:mo.span()[1]]

	f=open('data/pages/coinotron.html')
	s=f.read()
	r=re.compile(r'(?s)<tr.*?>\s*<td.*?>\s*BTC\s*</td>\s*<td.*?>\s*[0-9]{1,3}[.][0-9]{1,4}\s*[TGM]?H\s*</td>\s*<td.*?>'+r'[0-9]{1,4}\s*[BbMmKk]?')
	mo = r.search(s)
	print s[mo.span()[0]:mo.span()[1]]

	f=open('data/pages/coinotron.html')
	s=f.read()
	r=re.compile(r'<tr.*?>\s*<td.*?>\s*BTC\s*</td>\s*<td.*?>\s*')
	mo = r.search(s)
	print s[mo.span()[0]:mo.span()[1]]

