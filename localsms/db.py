from sqlobject import SQLObject, StringCol, IntCol, BoolCol, \
    TimeCol


class ModemLog(SQLObject): 
    time = StringCol() 
    modem = StringCol()
    msg = StringCol()
    msgType = StringCol() 


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

