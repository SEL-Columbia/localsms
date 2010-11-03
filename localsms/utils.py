
import pygsm 
import datetime 
import ConfigParser
import httplib2

from localsms.db import ModemLog

def get_now():
    return datetime.datetime.now() 
    
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
