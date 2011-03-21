import base64
import httplib
import json
import sqlite3
import os
import shutil
import string
import sys
import time

def make_zotero_db(current_path):
    new_path = ''.join(['zotero',str(int(time.time())),'.db'])
    shutil.copyfile(current_path,new_path)
    return new_path

def find_zotero_db(dir):
    for dirname, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            if ('zotero.sqlite' == filename):
                return os.path.join(dirname, filename)

def get_items(db_file):
    all = []
    conn = sqlite3.connect(db_file)
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
    
        item_collections_c = conn.cursor()
        sql = "SELECT collectionID FROM collectionItems WHERE itemID = ?"
        item_collections_c.execute(sql,(itemID,))
        item_meta['folder'] = [] 
        for collection_row in item_collections_c:
            collectionID = ''
            (collectionID,) = collection_row
            collections_c = conn.cursor()
            sql = "SELECT collectionName FROM collections WHERE collectionID = ?"
            collections_c.execute(sql,(collectionID,))
            (collectionName,) = collections_c.fetchone()
            item_meta['folder'].append(collectionName) 

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
    
        item = {}
        item['item_type'] = typeName
        item['metadata'] = item_meta
        item['key'] = key
        if 'title' in item['metadata']:
            item['title'] = item['metadata']['title'][0]
        else:
            item['title'] = key
        all.append(item)
    return all

def post_item(item_json):
    DASE_HOST = 'daseupload.laits.utexas.edu'
    h = httplib.HTTPSConnection(DASE_HOST,443)
    auth = 'Basic ' + string.strip(base64.encodestring('pkeane:pubsub'))
    body = item_json                                   
    headers = {
        "Content-Type":'application/json',
        "Content-Length":str(len(body)),
        "Authorization":auth
    };
    h.request("POST",'/collection/ut_publications?auth=service',body,headers)
    r = h.getresponse()
    return r.status



if __name__=="__main__":
    ZOTERO_DIR = '../Library/Application Support/Firefox'
    ZOTERO_DIR = '../.mozilla'
    already_uploaded = {}
    try:
        f = open('checklist.json','r')
        already_uploaded = json.load(f)
        f.close()
    except:
        pass
    #print type( already_uploaded)
    #sys.exit()
    zpath = find_zotero_db(ZOTERO_DIR)
    if not zpath:
        print "No Zotero found.  Is ZOTERO_DIR set correctly?"
        sys.exit()
    db_file = make_zotero_db(zpath)
    for item in get_items(db_file):
        print item['item_type'],item['key'],item['title']
        if item['key'] in already_uploaded:
            print "already uploaded"
        else:
            already_uploaded[item['key']] = item['title']
            print post_item(json.dumps(item))
    f = open('checklist.json','w')
    json.dump(already_uploaded,f)
    f.close()
