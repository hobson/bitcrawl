
import json
from pprint import pprint

json_data=open('bitcrawl_historical_data.json')

data = json.load(json_data)

pprint(data) # ADDS a U' in front of all items WHY?

json_data.close()
#data is a list of dictionaries obtained from the json file

#now creating a keylist
keylist = []
for item in data:
    itemkey = item.keys()
    keylist = keylist + itemkey
#print keylist
#keylist is the list of keys from the list of dictionaries

def bycol_key(data, key):#function for returning values given a key of the dictioanry data
    resultlist=[]
    col =[]
    for i in range (len(data)):#index loops thru each data item which are dictionaries
        item = data[i]
        if key in data[i]:
            #print item[key]
            col.append(item[key]['datetime'])#as sample we extract the value for 'datetime'           
    resultlist.append(col)
    return resultlist

#run it for a sample key 'mtgox' to get its datetime
listoflist = bycol_key(data,'mtgox')
pprint(listoflist)


#prints for mtgox the datetime is returned with a u' in front-why?
#[[u'2012-04-15 00:50:07.514000+05:30']]

#todo-
#1)quantities for a keyword: each key like mtgox has many numbers, so i read all of them?
#and the quantities varies for each key
#2)and i am having diffulty in putting them in "columns" of list of lists
