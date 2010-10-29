import os
import time
import datetime 

import ConfigParser
import simplejson
import pygsm 
from sqlobject import connectionForURI, sqlhub  
import httplib2

from localsms.db import Message, Log


def initdb(config,destructive=True):
    dbfile = os.path.abspath(
        config.get("app","db_params"))
    if os.path.exists(dbfile): 
        if destructive: 
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

def make_http(config): 
    h = httplib2.Http() 
    h.add_credentials(
        config.get("gateway","username"),
        config.get("gateway","password"))
    return h 

def send_sms_out(config,msg):
    """
    Makes an http request to send the message to a webserver
    """
    http = make_http(config)
    resp, content = http.request(
        "http://%s:%s/sms/send/" % ( 
          config.get("gateway","host"),
          config.get("gateway","port"),
          ) ,
        "POST", body=simplejson.dumps(msg.toJson()), 
        headers={'content-type':'text/json'} )
    print resp

def send_messages(config,modem): 
    """
    Send messages to the modem, checks the database for unprocesses messages
    """

def get_messages(config,modem): 
    """
    Takes messages off of the modem
    """
    gsmMsg = modem.next_message()
    if gsmMsg:
        msg = Message(
            sent=False,
            time=datetime.datetime.now(),
            text=gsmMsg.text,
            origin=int(gsmMsg.sender))
        send_sms_out(config,msg)
    

def main(*args): 
    print("booting message pool system") 
    config = get_config("localsms.ini") 
    initdb(config) 
    modem = get_modem(config) 
    while True: 
        print("running message pool system %s" % datetime.datetime.now()) 
        get_messages(config,modem)
        send_messages(config,modem) 
        time.sleep(
            float(config.get("app","modem_poll"))) # put to sleep the poll 
