import sys
import logging
import datetime 
import ConfigParser
import urllib2
from serial.serialutil import SerialException
import pygsm 
import httplib2
from localsms.db import ModemLog


def make_logger(config=None,name=None):                 
    log = logging.getLogger(name) 
    log.setLevel(logging.DEBUG)
    ch = logging.FileHandler(config.get("app","log_file"))
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(ch)
    return log

    
def ping_remote(config=None,log=None):
    """
    Check to see if the remote server is runnning.
    """
    try: 
        response = urllib2.urlopen(
            "http://%s:%s/sms/ping" % (
                config.get("remote","host"),
                config.get("remote","port")))
        if response.code == 200:  # make sure response is a 200 not 405 
            return True
        else: 
            return False 
    except Exception,e: 
        log.error(e) 
        return False

    
def make_modem_log(modem,msg,msgType): 
    ModemLog(time=str(datetime.datetime.now()),
        modem=str(modem),
        msg=str(msg),
        msgType=str(msgType))

def get_modem(config,log): 
    try:
        log.info("Trying to connect to the modem")
        return pygsm.GsmModem(
            port=config.get("modem","port"),
            logger=make_modem_log,
            baudrate=config.get("modem","baudrate"))
    except SerialException,e:
        log.error("Unable to conntect to the modem %s "% e)
        sys.exit(0)

def get_config(path): 
    config = ConfigParser.RawConfigParser()
    config.read(path) 
    return config 

def make_http(config): 
    h = httplib2.Http() 
    h.add_credentials(
        config.get("remote","username"),
        config.get("remote","password"))
    return h 
