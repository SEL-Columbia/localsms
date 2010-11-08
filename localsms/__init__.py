import time
from optparse import OptionParser
from localsms.db import initdb
from localsms.utils import get_modem, get_config,make_logger, \
    ping_remote
from localsms import gsmmodem
from localsms import remote 

        
def start_service(config=None,modem=None,log=None): 
    log.info("Running messaging pooling") 
    while True:                 
        if ping_remote(config=config,log=log):
            gsmmodem.get_message(config=config,modem=modem,log=log)
            gsmmodem.send_local_messages(config=config,modem=modem,log=log)
            remote.get_message(config=config,log=log) 
            remote.send_local_messages(config=config,modem=modem,log=log)
        else: 
            log.error("Unable to reach remote server")
            gsmmodem.get_message(config=config,modem=modem,log=log)
            gsmmodem.send_local_messages(config=config,modem=modem,log=log)
        time.sleep(int(config.get("app","poll")))
        

def main(*args): 
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                      help="config file")
    (options,args) = parser.parse_args() 

    config = get_config(options.config)
    log = make_logger(config=config,name="localsms.app.main")
    log.info("Booting messaging system")
    initdb(config)
    start_service(config=config,modem=get_modem(config,log),log=log)


