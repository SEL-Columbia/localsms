import os

from sqlobject import connectionForURI, sqlhub  
from sqlobject import SQLObject, StringCol, IntCol, BoolCol, \
    TimeCol, ForeignKey, EnumCol


class ModemLog(SQLObject): 
    time = StringCol() 
    modem = StringCol()
    msg = StringCol()
    msgType = StringCol() 

class MessageState(SQLObject):
    time = StringCol() 
    message = ForeignKey("Message") 
    state = EnumCol(enumValues=('new')) 
    
class Message(SQLObject):
    uuid = StringCol()
    source = StringCol() 
    text = StringCol()
    origin = IntCol(notNone=False)
    dest = IntCol(notNone=True) 
    sent = BoolCol()     
    time = TimeCol() 
    
    def toJson(self): 
        return { "text" : self.text, 
                 "uuid" : self.uuid,
                 "time" : str(self.time),
                 "from" : self.origin } 


def initdb(config):
    dbfile = os.path.abspath(
        config.get("app","db_params"))
    conn = connectionForURI(
        "%s:%s" % (config.get("app","db_type"),
                   dbfile))
    sqlhub.processConnection = conn
    Message.createTable(ifNotExists=True)
    ModemLog.createTable(ifNotExists=True) 
    MessageState.createTable(ifNotExists=True)
