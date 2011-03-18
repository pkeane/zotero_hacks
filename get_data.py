import json
import sqlite3
import os
import shutil
import sys
import time


dir = '../Library/Application Support/Firefox'
for dirname, dirnames, filenames in os.walk(dir):
    for filename in filenames:
        if ('zotero.sqlite' == filename):
            dbfile = os.path.join(dirname, filename)
            new = ''.join(['zotero',str(int(time.time())),'.db'])
            shutil.copyfile(dbfile,new)


conn = sqlite3.connect(new)
items_c = conn.cursor()
sql = "SELECT key,itemID,itemTypeID FROM items ORDER BY dateAdded DESC"
items_c.execute(sql)
for item_row in items_c:
    key = itemID = itemTypeID = ''
    (key,itemID,itemTypeID) = item_row
    print key
    item_creators_c = conn.cursor()
    sql = "SELECT creatorID,creatorTypeID FROM itemCreators WHERE itemID = ?"
    item_creators_c.execute(sql,(itemID,))
    for creator_row in item_creators_c:
        creatorID = creatorTypeID = creatorDataID = ''
        (creatorID,creatorTypeID) = creator_row
        creators_c = conn.cursor()
        sql = "SELECT creatorDataID FROM creators WHERE creatorID = ?"
        creators_c.execute(sql,(creatorID,))
        (creatorDataID,) = creators_c.fetchone()
        creatordata_c = conn.cursor()
        sql = "SELECT firstName,lastName FROM creatorData WHERE creatorDataID = ?"
        creatordata_c.execute(sql,(creatorDataID,)) 
        for creator_data in creatordata_c:
            firstName = lastName = ''
            (firstName,lastName) = creator_data
            print firstName,lastName




