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

all = []
conn = sqlite3.connect(new)
items_c = conn.cursor()
sql = "SELECT key,itemID,itemTypeID FROM items ORDER BY dateAdded DESC"
items_c.execute(sql)
for item_row in items_c:
    item_meta = {}
    item_meta['key'] = [] 
#    item_meta['notes'] = [] 
    item_meta['tags'] = [] 
    key = itemID = itemTypeID = ''
    (key,itemID,itemTypeID) = item_row
    item_meta['key'].append(key)
    item_creators_c = conn.cursor()
    sql = "SELECT creatorID,creatorTypeID, orderIndex FROM itemCreators WHERE itemID = ?"
    item_creators_c.execute(sql,(itemID,))
    item_meta['creator'] = [] 
    for creator_row in item_creators_c:
        creatorID = creatorTypeID = creatorDataID = orderIndex = ''
        (creatorID,creatorTypeID,orderIndex) = creator_row
        if 'creator'+str(orderIndex) not in item_meta:
            item_meta['creator'+str(orderIndex)] = [] 
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
            item_meta['creator'].append(lastName+' '+firstName)
            item_meta['creator'+str(orderIndex)].append(lastName+' '+firstName)

    item_data_c = conn.cursor()
    sql = "SELECT fieldID,valueID FROM itemData WHERE itemID = ?"
    item_data_c.execute(sql,(itemID,))
    for data_row in item_data_c:
        fieldID = valueID = value = ''
        (fieldID,valueID) = data_row
        field_c = conn.cursor()
        sql = "SELECT fieldName FROM fields WHERE fieldID = ?"
        field_c.execute(sql,(fieldID,))
        (fieldName,) = field_c.fetchone()
        if fieldName not in item_meta:
            item_meta[fieldName] = [] 
        value_c = conn.cursor()
        sql = "SELECT value FROM itemDataValues WHERE valueID = ?"
        value_c.execute(sql,(valueID,)) 
        (value,) = value_c.fetchone()
        try:
            item_meta[fieldName].append(str(value))
        except:
            item_meta[fieldName].append(value.encode('utf8'))

#    item_notes_c = conn.cursor()
#    sql = "SELECT note,title FROM itemNotes WHERE itemID = ?"
#    item_notes_c.execute(sql,(itemID,))
#    for notes_row in item_notes_c:
#        note = title = ''
#        (note,title) = notes_row
#        item_meta['notes'].append('['+title+'] '+note)

    item_meta['itemType'] = []
    item_type_c = conn.cursor()
    sql = "SELECT typeName FROM itemTypes WHERE itemTypeID = ?"
    item_type_c.execute(sql,(itemTypeID,))
    typeName = ''
    (typeName,) = item_type_c.fetchone()
    item_meta['itemType'].append(typeName)

    item_tags_c = conn.cursor()
    sql = "SELECT tagID FROM itemTags WHERE itemID = ?"
    item_tags_c.execute(sql,(itemID,))
    for tag_row in item_tags_c:
        tagID = ''
        (tagID,) = tag_row
        tag_c = conn.cursor()
        sql = "SELECT name FROM tags WHERE tagID = ?"
        tag_c.execute(sql,(tagID,))
        (name,) = tag_c.fetchone()
        item_meta['tags'].append(name)
    all.append(item_meta)

print json.dumps(all)

