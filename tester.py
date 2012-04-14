#!/usr/bin/env python

f=open('test_pages/virwox.html')
s=f.read()
import re
r=re.compile(r"<tr.*?>USD/SLL</th.*?><td.*?'buy'.*?>[0-9]{1,6}[.]?[0-9]{0,3}")
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]

r=re.compile(r"(?s)<fieldset>\s*<legend>\s*Trading\s*Volume\s*\(SLL\)\s*</legend>\s*<table.*?>\s*<tr.*?>\s*<td>\s*<b>\s*24\s*[Hh]ours\s*[:]?\s*</b>\s*</td>\s*<td>")
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]

f=open('test_pages/consultancy.html')
s=f.read()
r=re.compile(r'has\sbeen\saccessed\s([0-9]{1,3}[,]?){1,4}')
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]


f=open('test_pages/mtgox.html')
s=f.read()
r=re.compile(r'Volume\s*:\s*<span>\s*'+r'[0-9]{1,9}')
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]

f=open('test_pages/coinotron.html')
s=f.read()
r=re.compile(r'(?s)<tr.*?>\s*<td.*?>\s*BTC\s*</td>\s*<td.*?>\s*[0-9]{1,3}[.][0-9]{1,4}\s*[TGM]?H\s*</td>\s*<td.*?>'+r'[0-9]{1,4}\s*[BbMmKk]?')
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]

f=open('test_pages/coinotron.html')
s=f.read()
r=re.compile(r'<tr.*?>\s*<td.*?>\s*BTC\s*</td>\s*<td.*?>\s*')
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]

