import mysql.connector
from datetime import datetime,date,timedelta
from os import system

class Records:
    conn = mysql.connector.connect(user='southwest', database='Southwest')
    cur = conn.cursor(buffered=True)
    def setUser(self,user):
        query="REPLACE INTO Users VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cur.execute(query,user.getTuple())
    def getUser(self,chatID):
        query="SELECT  Users.ID, `Username`, `Password`, `FirstName`, `LastName`, `TelegramChatID`, `StartDateDefaultDelta`, `EndDateDefaultDelta`, `PriceDelta`, `MinPrice` FROM `Users` WHERE TelegramChatID=%s LIMIT 1"
        self.cur.execute(query,(chatID,))
        for row in self.cur:
            return self._createUser(row)
    def getUsers(self):
        query="SELECT  Users.ID, `Username`, `Password`, `FirstName`, `LastName`, `TelegramChatID`, `StartDateDefaultDelta`, `EndDateDefaultDelta`, `PriceDelta`, `MinPrice` FROM `Users` "
        self.cur.execute(query)
        users=[]
        for row in self.cur:
            users.append(self._createUser(row))
        return users
    def _createUser(self,args):
        userID,username,password,firstName,lastName,chatID, defaultDeltaStart,defaultDeltaEnd,priceDelta,minPrice=args
        return User(userID,username,password,firstName,lastName,chatID, defaultDeltaStart,defaultDeltaEnd,priceDelta,minPrice)
        
    def getSavedUpComingFlights(self,userID):
        query="SELECT FlightNumber, DepartureTime,Price,StartDate,EndDate FROM UpcomingFlights WHERE UserID=%s AND DepartureTime > NOW()"
        self.cur.execute(query,(userID,))
        savedUpComingFlights={}
        for flightNumber,departureTime,price,startDate,endDate in self.cur:
            savedUpComingFlights[Flight(flightNumber,departureTime=departureTime,arrivalTime=departureTime)]= price,startDate,endDate
        return savedUpComingFlights
    
    def saveNewFlight(self,userID,flight):
        query="REPLACE INTO `UpcomingFlights` (`UserID`, `ConfirmationNumber`, `FlightNumber`, `DepartureTime`, `ArrivalTime`, `Price` ) VALUES (%s,%s,%s,%s,%s,%s)"
        self.cur.execute(query,(userID,flight.confirmationNumber,flight.flightNumber,flight.departureTime,flight.arrivalTime,flight.price))
        
    def saveCheapFlights(self,cheaperFlights):
        query="REPLACE INTO `CheapFlights`(`DepartureTime`, `FlightNumber`, `Price` ) VALUES (%s,%s,%s)"
        for flight in cheaperFlights:
            self.cur.execute(query,(flight.departureTime,flight.flightNumber,flight.price))
        
    def getCheapFlights(self):
        query="SELECT  DepartureTime, `FlightNumber`, `Price` FROM CheapFlights WHERE DepartureTime > NOW()"
        self.cur.execute(query)
        cheaperFlights={}
        for departureTime,flightNumber,price in self.cur:
            cheaperFlights[Flight(flightNumber,departureTime=departureTime,arrivalTime=departureTime)]=price
        return cheaperFlights
    def commit(self):
        self.conn.commit()
    def close(self):
        self.cur.close()
        self.conn.close()
        
    @staticmethod
    def convertToLocalTime(date,airport):
        return date+timedelta(hours=Records.getOffset(date,airport))
    @staticmethod
    def getOffset(date,airport):
        if airport=="BOS":
            return -1
        elif airport=="SOF":
            return +2
        else:
            return 0
            
class Flight:
    def __init__(self,flightNumber,departureTime,arrivalTime,origin=None,dest=None, confirmationNumber=None,price=None,startDate=None,endDate=None,title=None):
        self.title=title
        self.confirmationNumber=confirmationNumber
        self.departureTime=departureTime
        self.arrivalTime=arrivalTime
        self.origin=origin
        self.dest=dest
        self.flightNumber=int(flightNumber)
        self.setMetadata(price,startDate,endDate)
        
    def setMetadata(self,price,startDate,endDate):
        self.price=price
        self.startDate=startDate
        self.endDate=endDate
    def getIdentifier(self):
        return self.flightNumber,self.departureTime
    def shouldSetCheckinTimer(self,database=None):        
        return (database.convertToLocalTime(self.departureTime,self.origin)-datetime.now()).days==1
    def setCheckinTimer(self,user):
        setCheckinTimer(self.confirmationNumber, user.firstName, user.lastName,user.id, self.departureTime.strftime("%H%M"))
    def __hash__(self):
        return hash(self.getIdentifier())
    def __eq__(self,other):
        return other.getIdentifier and other.getIdentifier()==self.getIdentifier()
    def __ne__(self,other):
        return not self.__eq__(other)
    def __lt__(self, other):
        return self.price<other.price
    def __str__(self):
        return "#%d %s-%s %s to %s" % (self.flightNumber,self.departureTime.strftime("%b %d %y %H:%M"),self.arrivalTime.strftime("%H:%M"),self.origin,self.dest)
    def getDate(self):
        return datetime.date(self.departureTime)
    def getDates(self):
        dateRange=list(range(-self.startDate,self.endDate))
        dateRange.sort(key=lambda x:abs(x))
        date=self.getDate()
        return list(map(lambda x:date-timedelta(x),dateRange))
    def getDateString(self):
        return self.departureTime.strftime("%m/%d/%Y")
    
class ScannedFlight(Flight):
    def __init__(self,flightNumber,departureTime,arrivalTime,price,routing,flight):
        super().__init__(flightNumber=flightNumber,departureTime=departureTime,arrivalTime=arrivalTime, origin=flight.origin,dest=flight.dest,price=price)
        self.routing=routing.split("\n")[0].strip()
    def __str__(self):
        return super().__str__()+" $%d %s" % (self.price,self.routing)
    
        
class User:
    def __init__(self,userID,username,password,firstName,lastName,chatID, defaultDeltaStart=7,defaultDeltaEnd=7,priceDelta=5,minPrice=2000):
        self.id=int(userID)
        self.username=username
        self.password=password
        self.firstName=firstName
        self.lastName=lastName
        self.chatID=chatID
        self.defaultDeltaStart=defaultDeltaStart
        self.defaultDeltaEnd=defaultDeltaEnd
        self.priceDelta=float(priceDelta)
        self.minPrice=float(minPrice)
    def getTuple(self):
        return self.id, self.username, self.password, self.firstName, self.lastName, self.chatID, self.defaultDeltaStart, self.defaultDeltaEnd, self.priceDelta, self.minPrice
    def __str__(self):
        return self.username
    def whoami(self):
        return "username:%s password:%s firstName:%s lastName:%s defaultDeltaStart:%s defaultDeltaEnd:%s priceDelta:%s minPrice:%s" % (self.username, self.password, self.firstName, self.lastName, self.defaultDeltaStart, self.defaultDeltaEnd, self.priceDelta, self.minPrice)

def setCheckinTimer(confirmationNumber,firstName,lastName,time):
        return system("echo 'southwest-bot checkin %s %s %s %s' | at %s" % (confirmationNumber,firstName,lastName,time))
