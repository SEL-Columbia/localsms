import os
import time
import datetime 

import ConfigParser
import simplejson

import pygsm 
from sqlobject import connectionForURI, sqlhub  
import httplib2

from localsms.models import Message, Log


def initdb(config): 
    dbfile = os.path.abspath(
        config.get("app","db_params"))
    if os.path.exists(dbfile): 
        os.remove(dbfile)    
    conn = connectionForURI(
        "%s:%s" % (config.get("app","db_type"),
                   dbfile))
    sqlhub.processConnection = conn
    Message.createTable()
    Log.createTable() 
    
def log(modem,msg,msgType): 
    Log(time=str(datetime.datetime.now()),
        modem=str(modem),
        msg=str(msg),
        msgType=str(msgType))

def get_modem(config): 
    return pygsm.GsmModem(
        port=config.get("app","modem_port"),
        logger=log,
        baudrate=config.get("app","modem_baudrate"))

def get_config(path): 
    config = ConfigParser.RawConfigParser()
    config.read(path) 
    return config 

def send_sms_out(config,msg):    
    h = httplib2.Http() 
    h.add_credentials(
        config.get("gateway","username"),
        config.get("gateway","password"))
    resp, content = h.request(
        "http://%s/sms/send/" % config.get("gateway","host"),
        "POST", body=simplejson.dumps(msg.toJson()), 
        headers={'content-type':'text/json'} )
    print resp

def send_messages(config,modem): 
    pass 

def get_messages(config,modem): 
    gsmMsg = modem.next_message()
    if gsmMsg:
        msg = Message(
            text=gsmMsg.text,
            origin=int(gsmMsg.sender))
        send_sms_out(config,msg)
    

def main(*args): 
    config = get_config("localsms.ini") 
    initdb(config) 
    modem = get_modem(config) 
    while True: 
        get_messages(config,modem)
        send_messages(config,modem) 
        time.sleep(3) # put to sleep the poll 
