#!/usr/bin/env python

f=open('test_pages/virwox.html')
s=f.read()
import re
r=re.compile(r"<tr.*?>USD/SLL</th.*?><td.*?'buy'.*?>[0-9]{1,6}[.]?[0-9]{0,3}")
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]

f=open('test_pages/consultancy.html')
s=f.read()
r=re.compile(r'has\sbeen\saccessed\s([0-9]{1,3}[,]?){1,4}')
mo = r.search(s)
print s[mo.span()[0]:mo.span()[1]]




