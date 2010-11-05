"""


""" 
import uuid
import datetime
from pygsm.errors import GsmReadError

from localsms.db import Message
from localsms import remote 


def send_local_messages(config=None,modem=None,log=None):
    """
    Query database to find message that need to be sent via
    the modem.
    """
    unsentMsgs = Message.selectBy(sent=False,source="http")
    if unsentMsgs.count() > 0:
        log.info("Unsent messages %s" % unsentMsgs.count())
        for msg in unsentMsgs:
            send_message(
                modem=modem,
                log=log,
                msg=msg) 



def get_message(config=None,modem=None,log=None): 
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
            remote.send_message(config,msg,log)
    except GsmReadError:
        log.error("Error talking to modem skipping and trying again.")


def send_message(modem=None,log=None,msg=None): 
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

