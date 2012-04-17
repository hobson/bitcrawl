
import json
from pprint import pprint
import datetime

json_data=open('bitcrawl_historical_data.json')

data = json.load(json_data)
#if not data: gives error why? -so commented out
#    return data

#pprint(data) # ADDS a U' in front of all items WHY? because U=unicode format

json_data.close()
#data is a list of dictionaries obtained from the json file

#now creating a keylist
keylist = []
for item in data:
    itemkey = item.keys()
    keylist = keylist + itemkey
#print keylist
#keylist is the list of keys from the list of dictionaries

def bycol_key(data, key):#function for returning values given a key of the dictionary data
    columns =[]
    for record in data:#index loops thru each data item which are dictionaries
        #for all keys like mtgox use -- for key in keylist
        if key in record.keys():
            keyrecord = record[key]  
            #print 'keyrecord=',keyrecord
            columns.append([])# add an empty row
            if 'datetime' in keyrecord.keys():
            # add the time to the empty row
            # leave it as a string and I'll convert to a value
                dt = datetime.datetime.strptime(keyrecord['datetime'][0:-6],"%Y-%m-%d %H:%M:%S.%f")
                dt_value = float(dt.toordinal())+dt.hour/24.+dt.minute/24./60.+dt.second/24./3600.
                columns[-1].append(dt_value)
            if 'average' in keyrecord.keys():
                # float() won't work if there's a dollar sign in the price
                value = float(keyrecord['average'].strip().strip('$').strip())
                # add the value to the last row
                columns[-1].append(value)
        #pprint(columns,indent=2)       
        return columns

#run it for a sample key 'mtgox' to get its datetime and average intoa list of list
listoflist = bycol_key(data,'mtgox')
pprint(listoflist)
#[[734608.0348032408, 4.95759]]

#prints for mtgox the datetime key is returned with a u in front of strings like key names, but not before numbers
#-why? answer:- u indicates Unicode formatted strings returned by json decoder



