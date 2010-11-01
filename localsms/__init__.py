
import os,sys 
import time
import datetime 
import threading
import logging
import ConfigParser
import uuid
import urllib2
from optparse import OptionParser


import simplejson
import pygsm 
import httplib2
from sqlobject import connectionForURI, sqlhub  
from dateutil.parser import parse as time_parse

from localsms.db import Message, ModemLog


def initdb(config):
    dbfile = os.path.abspath(
        config.get("app","db_params"))
    conn = connectionForURI(
        "%s:%s" % (config.get("app","db_type"),
                   dbfile))
    sqlhub.processConnection = conn
    Message.createTable(ifNotExists=True)
    ModemLog.createTable(ifNotExists=True) 
    
def make_modem_log(modem,msg,msgType): 
    ModemLog(time=str(datetime.datetime.now()),
        modem=str(modem),
        msg=str(msg),
        msgType=str(msgType))

def get_modem(config): 
    return pygsm.GsmModem(
        port=config.get("app","modem_port"),
        logger=make_modem_log,
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


def poll_remote_msgs(config,log):
    http = make_http(config)
    try:
        resp, content = http.request(
            "http://%s:%s/sms/received/" % 
            (config.get("gateway","host"),
             config.get("gateway","port")),
            "GET")
        if resp.status == 200:
            msgs = simplejson.loads(content)            
            #if len(msgs): log.info(msgs)
            for msg in msgs:
                Message(uuid=str(uuid.uuid4()),
                        sent=False,
                        source="http",
                        dest=int(msg["to"]),
                        time=time_parse(msg["time"]),
                        text=msg["text"],
                        origin=int(msg["from"]))
    except Exception, e:
        log.error(e)


def send_to_remote(config,msg,log):
    """
    Makes an http request to send the message to a webserver
    """
    try:
        http = make_http(config)
        resp, content = http.request(
            "http://%s:%s/sms/send/" % ( 
                config.get("gateway","host"),
                config.get("gateway","port"),          
                ),
            "POST",body=simplejson.dumps(msg.toJson()), 
            headers={'content-type':'text/json'})
        if resp.code == 200:
            msg.sent = True 
    except Exception,e: 
        log.error("Unable to send msg to remote host %s" % e)


def get_msg_modem(config,modem,log,connected=None): 
    """
    Takes messages off of the modem
    """
    gsmMsg = modem.next_message()   
    if gsmMsg:
        log.info("Got Message from Modem %s" % gsmMsg)
        msg = Message(
            uuid=str(uuid.uuid4()),
            sent=False,
            source="gsm",
            time=datetime.datetime.now(),
            text=gsmMsg.text,
            origin=int(gsmMsg.sender))
        if connected:
            send_to_remote(config,msg,log)


def send_to_modem(modem=None,log=None,msg=None): 
    """
    Send messages to the modem,
    """
    try: 
        modem.send_sms(str(msg.dest),str(msg.text)) 
        msg.sent = True
    except Exception,e:
        msg.sent = False 
        log.error("Error send to modem %s" % e) 


def get_and_send_cache(config=None,modem=None,log=None):
    """
    Query database to find message that need to be sent via
    the modem.
    """
    unsentMsgs = Message.selectBy(sent=False,source="http")
    if unsentMsgs.count() > 0:
        log.info("Unsent messages %s" % unsentMsgs.count())
        for msg in unsentMsgs:
            send_to_modem(modem=modem,
                          log=log,
                          msg=msg) 

    
def ping_remote(config=None,log=None):
    """
    Check to see if the remote server 
    """
    try: 
        response = urllib2.urlopen(
            "http://%s:%s/sms/" % (
                config.get("gateway","host"),
                config.get("gateway","port")))
        if response.code == 200:  # make sure response is a 200 not 405 
            return True
        else: 
            return False 
    except Exception,e: 
        log.error(e) 
        return False
        
    

def start_service(config=None,modem=None,log=None): 
    log.info("Running messaging pooling") 
    while True:         
        connected = ping_remote(config=config,
                                log=log)
        if connected:
            get_msg_modem(config=config,
                          modem=modem,
                          log=log,
                          connected=connected)  # why am i passing conn here? 
            get_and_send_cache(config=config,
                               modem=modem,
                               log=log)
            poll_remote_msgs(config=config,
                             log=log) 
        else: 
            log.error("Unable to reach remote server")
            get_msg_modem(config=config,
                          modem=modem,
                          log=log,
                          connected=connected)

        time.sleep(
            float(config.get("app","modem_poll")))
        


def make_logger(name=None):                 
    log = logging.getLogger(name) 
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(ch)
    return log

def main(*args): 
    log = make_logger(name="localsms.app.main")
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                      help="config file")
    (options,args) = parser.parse_args() 
    log.info("Booting messaging system")
    config = get_config(options.config) 
    initdb(config) 
    modem = get_modem(config) 
    start_service(config=config,
                  modem=modem,
                  log=log)


