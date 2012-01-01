#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
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

def attachFilesToMessages(msg, files):
    for f in files:
        part = MIMEBase('application', "octet-stream")
        content = open(f,"rb").read()
        print type(content)
        part.set_payload(content)
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(f))
        msg.attach(part)

def createMessage(to, subject):
    msg = MIMEMultipart()
    msg['From'] = FROM
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    return msg

def sendfiletokindle(files):
    import smtplib
    server = smtplib.SMTP( "smtp.gmail.com" )
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(FROM, FROM_PASSWORD)
    msg = createMessage([KINDLE_MAIL], "file-update")
    attachFilesToMessages(msg, files)
    print("sending %s to kindle" % files)
    server.sendmail(FROM, [KINDLE_MAIL], msg.as_string())
    server.close()
    
def smart_truncate(content, length=30, suffix='...'):
    if len(content) <= length:
        return content
    else:
        print "truncating " + content
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix

def get_immediate_subdirectories(dir):
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]

def main():
    x = None
    env = os.environ
    if "DISPLAY" not in env:
        print "starting temporary Xserver"
        x = subprocess.Popen("exec Xvfb :2 -screen 0 800x600x24", shell=True)
        env["DISPLAY"] = "localhost:2"
        
    files = []
    
    conn = sqlite3.connect("items.db")
    cursor = conn.cursor()

    items = cursor.execute("SELECT name FROM feeds").fetchall()
    print items
   
    for item in items:
        [folder] = item
        head = """<html>
        <head>
            <title>%s - %s</title>
        </head>
        <body>
        """ % (folder, time.strftime("%Y-%m-%d %H.%M.%S"))
        tail = "</body>\n</html>"
        index = "<ul>"
        content = ""
        i = 0
        obj = cursor.execute("SELECT id, title, date, content FROM items WHERE feedname = ? AND read='FALSE'", (folder, )).fetchall()
        #obj = [ name for name in os.listdir(folder) if name.endswith(".json") ]
        if len(obj) == 0:
            continue

        for itemfile in obj:
            [i, itemtitle, itemdate, itemcontent] = itemfile

            index += "<li>%s: <a href=\"#i%d\">%s</a></li>\n" % (itemdate, i, itemtitle)
            content +=  "<a name=\"i%d\"><h1>%s</h1></a>\n" % (i, itemtitle)
            content += itemcontent
            content += "<br/><hr/><br/>"
            cursor.execute("UPDATE items SET read='TRUE' WHERE id=?", (i, ))
        index += "</ul>"

        fname = "%s-%s.html" % (folder, time.strftime("%Y-%m-%d_%H.%M.%S"))
        f = codecs.open(fname, 'w', encoding='utf-8')
        f.write(head)
        f.write(index)
        f.write(content)
        f.write(tail)
        f.close()
        
        mobiname = re.sub(".html$", ".mobi", fname)
            
        subprocess.call( ["ebook-convert", fname, mobiname] , env = env)
        files.append(mobiname)
        conn.commit()
            
    if x != None:
        x.terminate()

    if len(files) == 0:
        return

    sendfiletokindle(files)
        
if __name__ == "__main__":
    main()
