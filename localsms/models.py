from sqlobject import SQLObject, StringCol, IntCol 


class Log(SQLObject): 
    time = StringCol() 
    modem = StringCol()
    msg = StringCol()
    msgType = StringCol() 


class Message(SQLObject):
    text = StringCol()
    origin = IntCol(notNone=False)
    
    def toJson(self): 
        return { "text" : self.text, "from" : self.origin } 

