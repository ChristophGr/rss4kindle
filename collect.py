#!/usr/bin/env python
# -*- coding: utf-8 -*-
import feedparser
import re, datetime, time
import smtplib
import codecs

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

import os, sys, subprocess
from util import *
from config import *
from parserconfig import *
from StringIO import StringIO

def parsefeed(feed):
    print "parsing feed: " + feed.feed.title
    newitems = []
    for item in feed["items"]:
        idate = item.date_parsed
        datestring = time.strftime("%d.%m.%Y %H:%M:%S", idate)
        item_html = "<div>%s</div><br/>\n" % datestring

        if feed.feed.title in LINK_PARSERS:
            item_html = LINK_PARSERS[feed.feed.title](item)
        elif "content" in item:
            for citem in item["content"]:
                item_html += citem.value + "\n"
        elif "summary_detail" in item:
            item_html += item.summary_detail.value + "\n"
        else:
            item_html += "<p>no content</p>"

        from lxml import etree
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(item_html), parser)
        res = tree.xpath('//img')
        for x in res:
            print "found image %s" % etree.tostring(x, pretty_print=True)
            originalSource = x.get("src")
            if originalSource[0] == "/":
                x.clear()
                continue
            filename = download(originalSource)
            x.set("src", filename)
        item_html = etree.tostring(tree, pretty_print=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S.0", idate)
        newitems.append(dict(title = item.title, date = timestamp, content = item_html))
    return newitems
    
def initTables(cursor):
    existing = cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' and name = 'items'").fetchone()
    if existing:
        return
    cursor.execute("CREATE TABLE items(id INTEGER PRIMARY KEY AUTOINCREMENT, feedname VARCHAR, date TIMESTAMP, title VARCHAR, author VARCHAR, content VARCHAR, read BOOLEAN default FALSE)")
    cursor.execute("CREATE TABLE feeds(name VARCHAR PRIMARY KEY)")
    
def main():
    import sqlite3
    conn = sqlite3.connect("items.db")
    cursor = conn.cursor()

    initTables(cursor)
    
    for url in FEEDURLS:
        feed = feedparser.parse( url )
        title = feed.feed.title
        existing = cursor.execute("SELECT * FROM feeds WHERE name==?", (title,)).fetchone()
        if not existing:
            print "inserting " + title
            cursor.execute("INSERT INTO feeds(name) VALUES (?)", (title, ))
        
        feedcontent = parsefeed(feed)
        #if not os.path.exists(title):
            #os.mkdir(title)
        for item in feedcontent:
            if cursor.execute("SELECT * FROM items WHERE feedname = ? AND date = ? AND title = ?", (title, item["date"], item["title"])).fetchone():
                print "skipping item " + item["title"]
                continue
            print "inserting new item " + item["title"]
            cursor.execute("INSERT INTO items(feedname, date, title, author, content) VALUES (?, ?, ?, ?, ?)", (title, item["date"], item["title"], "", item["content"],))
            conn.commit()

    cursor.close()
    conn.close()
        
if __name__ == "__main__":
    main()