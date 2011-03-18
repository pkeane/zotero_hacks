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
    creators_c = conn.cursor()
    sql = "SELECT creatorID,creatorTypeID FROM itemCreators WHERE itemID = ?"
    creators_c.execute(sql,(itemID,))
    for creator_row in creators_c:
        print creator_row


