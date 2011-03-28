#!/usr/bin/env python

try:
    import json
except:
    import simplejson as json
from operator import itemgetter, attrgetter
from random import randint
from tkFileDialog import askdirectory      
from tkFileDialog import askopenfilename      
from Tkinter import * 
from tkSimpleDialog import askstring
import base64
import copy
import fnmatch
import httplib
import md5
import mimetypes
import os
import shutil
import sqlite3
import string
import sys
import time
import tkFont 
import tkSimpleDialog
import urllib
import urllib2


DASE_HOST = 'daseupload.laits.utexas.edu'
DASE_BASE = '/'
PROTOCOL = 'https'

def rfc3339():
    """ Format a date the way Atom likes it (RFC3339)
    """
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')

class ScrolledText(Frame):
    """ from O'Reilly Programming Python 3rd ed.
    """
    def __init__(self, parent=None, text='', file=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)                 # make me expandable
        self.makewidgets()
        self.settext(text, file)
    def makewidgets(self):
        sbar = Scrollbar(self)
        text = Text(self, relief=SUNKEN,height=18)
        sbar.config(command=text.yview)                  # xlink sbar and text
        text.config(yscrollcommand=sbar.set)             # move one moves other
        sbar.pack(side=RIGHT, fill=Y)                    # pack first=clip last
        text.pack(side=LEFT, expand=YES, fill=BOTH)      # text clipped first
        self.text = text
    def addtext(self,text):
        self.text.insert(END,text)
        self.text.insert(END,"\n")
        self.update_idletasks()
        self.text.focus()                                # save user a click
        self.text.yview_pickplace("end")
    def settext(self, text='', file=None):
        if file: 
            text = open(file, 'r').read()
        self.text.delete('1.0', END)                     # delete current text
        self.text.insert('1.0', text)                    # add at line 1, col 0
        self.text.mark_set(INSERT, '1.0')                # set insert cursor
        self.text.focus()                                # save user a click
    def gettext(self):                                   # returns a string
        return self.text.get('1.0', END+'-1c')           # first through last

class Application():
    def __init__(self, master):

        self.eid = ''
        self.root = master
        frame = Frame(master)
        frame.pack(fill=BOTH,padx=2,pady=2)

        self.f1 = tkFont.Font(family="arial", size = "14", weight = "bold")
        self.titleLabel = Label(frame, width=66, padx = '3', pady = '3', font = self.f1,anchor=W)
        self.titleLabel.pack()

        self.report = ScrolledText(frame)

        menu = Menu(frame)
        self.menu = menu
        root.config(menu=menu)

        filemenu = Menu(menu)
        menu.add_cascade(label="Login/Exit", menu=filemenu)
        filemenu.add_command(label="Login", command=self.login_user)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)

        self.clear_button = Button(frame, text="Clear",command=self.clear)
        self.clear_button.pack(side=RIGHT)

        self.upload_button = Button(frame, text="Upload Recent Citations",command=self.upload)
        self.upload_button.pack(side=RIGHT)

        #self.login_button = Button(frame, text="Login",command=self.login_user)
        #self.login_button.pack(side=LEFT)

        self.write("Please login\n")
        self.frame = frame
        self.collection = ''
        self.user = ''

    def logout_user(self):
        pass

    def upload(self):
        if not self.eid:
            self.login_user()
        ZOTERO_DIR = '../Library/Application Support/Firefox'
        #ZOTERO_DIR = '../.mozilla'
        already_uploaded = {}
        try:
            f = open('checklist.json','r')
            already_uploaded = json.load(f)
            f.close()
        except:
            pass
        zpath = self.find_zotero_db(ZOTERO_DIR)
        if not zpath:
            self.write("No Zotero found.  Is ZOTERO_DIR set correctly?")
            sys.exit()
        db_file = self.make_zotero_db(zpath)
        for item in self.get_items(db_file):
            self.write(item['item_type']+' '+item['key'])
            self.write(item['title'])
            if item['key'] in already_uploaded:
                self.write("already uploaded")
            else:
                already_uploaded[item['key']] = item['title']
                self.write(self.post_item(json.dumps(item)))
        f = open('checklist.json','w')
        json.dump(already_uploaded,f)
        f.close()

    def login_user(self):
        eid = askstring('enter your EID','EID')
        self.eid = eid
        self.write(eid+' is logged in')
        self.logout_button = Button(self.frame, text="Logout "+eid,command=self.logout_user)
        self.logout_button.pack(side=LEFT)

    def write(self,text,delete_text=False):
        if delete_text:
            self.report.settext(text)
        else:
            self.report.addtext(text)

    def clear(self):
        self.report.settext('')

    def checkMd5(self,coll,md5):
        h = self.getHTTP() 
        h.request("GET",DASE_BASE.rstrip('/')+'/collection/'+coll+'/items/by/md5/'+md5+'.txt')  
        r = h.getresponse()
        if 200 == r.status:
            self.write(r.read())
            return True
        else:
            return False

    def postFile(self,path,filename,DASE_HOST,coll,mime_type,u,p):
        auth = 'Basic ' + string.strip(base64.encodestring(u + ':' + p))
        f = file(path.rstrip('/')+'/'+filename, "rb")
        self.body = f.read()                                                                     
        h = self.getHTTP()
        headers = {
            "Content-Type":mime_type,
            "Content-Length":str(len(self.body)),
            "Authorization":auth,
            "Title":filename,
        };

        md5sum = md5.new(self.body).hexdigest()
        if not self.checkMd5(coll,md5sum):
            h.request("POST",DASE_BASE.rstrip('/')+'/media/'+coll,self.body,headers)
            r = h.getresponse()
            return (r.status)

    def getHTTP(self):
        if ('https' == PROTOCOL):
            h = httplib.HTTPSConnection(DASE_HOST,443)
        else:
            h = httplib.HTTPConnection(DASE_HOST,80)
        return h

    def abort_upload(self):
        self.root.destroy()

    def upload_files(self):
        self.write('processing files...')
        if not self.user:
            self.write('ERROR: please Login\n',True)
            return
        if not self.collection:
            self.write('ERROR: please select a collection\n',True)
            return
        for file in self.files:
            (mime_type,enc) = mimetypes.guess_type(self.dirpath+file)
            self.write("uploading "+file)
            self.frame.update_idletasks()
            status = self.postFile(self.dirpath,file,DASE_HOST,self.collection,mime_type,self.user,self.password)
            if (201 == status):
                self.write("server says... "+str(status)+" OK!!\n")
            else:
                self.write("problem with "+file+"("+str(status)+")\n")
            self.frame.update_idletasks()

        #FROM get_data.py

    def make_zotero_db(self,current_path):
        new_path = ''.join(['zotero',str(int(time.time())),'.db'])
        shutil.copyfile(current_path,new_path)
        return new_path
    
    def find_zotero_db(self,dir):
        for dirname, dirnames, filenames in os.walk(dir):
            for filename in filenames:
                if ('zotero.sqlite' == filename):
                    return os.path.join(dirname, filename)
    
    def get_items(self,db_file):
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
    
    def post_item(self,item_json):
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

if __name__ == "__main__":
    root = Tk()
    root.title('Zotero Poster')
    root.geometry('+25+25')
    app = Application(root)
    root.mainloop() 
