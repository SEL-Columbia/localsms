
import time
import datetime 
import logging
import uuid
import urllib2
from optparse import OptionParser

import simplejson
import pygsm
from dateutil.parser import parse as time_parse

from localsms.db import Message, initdb
from localsms.utils import make_http, get_modem, get_config


def remove_from_remote(config=None,log=None,message=None): 
    http = make_http(config)
    resp, content = http.request(
        "http://%s:%s/sms/message/%s/" % (
            config.get("gateway","host"),
            config.get("gateway","port"),
            message.uuid),
        "DELETE")
    log.info("Removing msg<%s> from the remote server " % message.uuid)

def poll_remote_msgs(config=None,log=None):
    http = make_http(config)
    try:
        resp, content = http.request(
            "http://%s:%s/sms/received/" % 
            (config.get("gateway","host"),
             config.get("gateway","port")),
            "GET")
        if resp.status == 200:
            remoteMsgs = simplejson.loads(content)            
            for remoteMsg in remoteMsgs:
                msg = Message(uuid=remoteMsg["uuid"],
                        sent=False,
                        source="http",
                        dest=int(remoteMsg["to"]),
                        time=time_parse(remoteMsg["time"]),
                        text=remoteMsg["text"],
                        origin=int(remoteMsg["from"]))
                log.info("Got msg<%s> from remote" % msg.uuid)
                remove_from_remote(
                    config=config,
                    log=log,
                    message=msg)
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
        msg.sent = True 
        log.info("%s:%s" % (resp,content))
        log.info("Sent msg<%s> to remote" % msg.uuid)
    except Exception,e: 
        log.error("Unable to send msg<%s> to remote host %s" % (msg,e))


def get_msg_from_modem(config=None,modem=None,log=None): 
    """
    Take messages off of the modem
    """
    try:
        gsmMsg = modem.next_message()   
        if gsmMsg:
            msg = Message(
                uuid=str(uuid.uuid4()),
                sent=False,
                dest=int(config.get("app","number")),
                source="gsm",
                time=datetime.datetime.now(),
                text=gsmMsg.text,
                origin=int(gsmMsg.sender))
            log.info("Got msg<%s> from modem" % msg.uuid)
            send_to_remote(config,msg,log)
    except pygsm.errors.GsmReadError:
        log.error("Error talking to modem skipping and trying again.")


def send_to_modem(modem=None,log=None,msg=None): 
    """
    Send messages to the modem,
    """
    try: 
        log.info("Trying to send msg<%s> to the modem" % msg.uuid) 
        modem.send_sms("+%s" % msg.dest,str(msg.text)) 
        msg.sent = True
        log.info("Sent msg<%s> to the modem" % msg.uuid)
    except Exception,e:
        msg.sent = False 
        log.error("Error sending msg<%s> to modem %s" % (msg.uuid,e)) 


def send_cache_modem(config=None,modem=None,log=None):
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

def send_cache_remote(config=None,modem=None,log=None): 
    """
    Sends to remote a local cache of messages
    """
    unsentMsgs = Message.selectBy(sent=False,source="gsm") 
    if unsentMsgs.count() > 0: 
        log.info("Unsent messages %s" % unsentMsgs.count())
        for msg in unsentMsgs:
            send_to_remote(
                config=config,
                log=log,
                msg=msg)

    
def ping_remote(config=None,log=None):
    """
    Check to see if the remote server is runnning.
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
        
        if ping_remote(config=config,log=log):

            get_msg_from_modem(
                config=config,
                modem=modem,
                log=log)

            send_cache_modem(
                config=config,
                modem=modem,
                log=log)

            send_cache_remote(
                config=config,
                modem=modem,
                log=log)

            poll_remote_msgs(
                config=config,
                log=log) 
        else: 
            log.error("Unable to reach remote server")
            get_msg_from_modem(
                config=config,
                modem=modem,
                log=log)

        time.sleep(int(config.get("app","poll")))
        


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


