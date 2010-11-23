import simplejson
from dateutil.parser import parse as time_parse
from localsms.utils import make_http
from localsms.db import Message


def send_local_messages(config=None,modem=None,log=None): 
    """
    Sends to remote a local cache of messages
    """
    unsentMsgs = Message.selectBy(sent=False,source="gsm") 
    if unsentMsgs.count() > 0: 
        log.info("Unsent messages %s" % unsentMsgs.count())
        for msg in unsentMsgs:
            send_message(
                config=config,
                log=log,
                msg=msg)



def remove_from_remote(config=None,log=None,message=None): 
    http = make_http(config)
    resp, content = http.request(
        "http://%s:%s/message/remove/%s" % (
            config.get("remote","host"),
            config.get("remote","port"),
            message.uuid),
        "POST")
    log.info("Removing msg<%s> from the remote server " % message.uuid)


def get_message(config=None,log=None):
    http = make_http(config)
    try:
        resp, content = http.request(
            "http://%s:%s/sms/received" % 
            (config.get("remote","host"),
             config.get("remote","port")),
            "GET")
        if resp.status == 200:
            remoteMsgs = simplejson.loads(content)            
            for remoteMsg in remoteMsgs:
                msg = Message(uuid=remoteMsg["uuid"],
                        sent=False,
                        source="http",
                        dest=int(remoteMsg["number"]),
                        time=time_parse(remoteMsg["time"]),
                        text=remoteMsg["text"],
                        origin=int(1))
                log.info("Got msg<%s> from remote" % msg.uuid)
                remove_from_remote(
                    config=config,
                    log=log,
                    message=msg)
    except Exception, e:
        log.error(e)




def send_message(config,msg,log):
    """
    Makes an http request to send the message to a webserver
    """
    try:
        http = make_http(config)
        resp, content = http.request(
            "http://%s:%s/sms/send" % ( 
                config.get("remote","host"),
                config.get("remote","port"),          
                ),
            "POST",body=simplejson.dumps(msg.toJson()), 
            headers={'content-type':'text/json'})
        msg.add_state("sent-to-remote")
        msg.sent = True 
        log.info("Sent msg<%s> to remote" % msg.uuid)
    except Exception,e: 
        log.error("Unable to send msg<%s> to remote host %s" % (msg,e))
