from sqlobject import SQLObject, StringCol, IntCol, BoolCol, \
    TimeCol


class Log(SQLObject): 
    time = StringCol() 
    modem = StringCol()
    msg = StringCol()
    msgType = StringCol() 


class Message(SQLObject):
    text = StringCol()
    origin = IntCol(notNone=False)
    sent = BoolCol() 
    time = TimeCol() 
    
    def toJson(self): 
        return { "text" : self.text, 
                 "time" : str(self.time),
                 "from" : self.origin } 

