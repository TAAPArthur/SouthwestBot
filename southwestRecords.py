import mysql.connector
from datetime import datetime,date,timedelta
from southwestObjects import Flight,User,ScannedFlight
class Records:
    
    def __init__(self):
        self.conn = mysql.connector.connect(user='southwest', database='Southwest')
        self.cur = self.conn.cursor(buffered=True)    
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
    
    def setSavedUpComingFlights(self,userID,flights):
        query="UPDATE UpcomingFlights SET `Active`=2 WHERE UserID=%s AND DepartureTime > NOW() AND Active=1"
        self.cur.execute(query,(userID,))
        query="UPDATE UpcomingFlights SET `Active`=1 WHERE UserID=%s AND Active=2 AND FlightNumber=%s AND DepartureTime=%s"
        for flight in flights:
            self.cur.execute(query,(userID,flight.flightNumber,flight.departureTime.strftime("%Y-%m-%d %H:%M:%S")))
        query="UPDATE UpcomingFlights SET `Active`=0 WHERE UserID=%s AND Active=2"
        self.cur.execute(query,(userID,))
    def updatePriceOfUpComingFlights(self,userID,flight):
        query="UPDATE UpcomingFlights SET `Price`=%s WHERE UserID=%s AND DepartureTime > NOW() AND Active=1 AND FlightNumber=%s AND DepartureTime=%s"
        self.cur.execute(query,(userID,flight.flightNumber,flight.departureTime.strftime("%Y-%m-%d %H:%M:%S")))
        
    def getSavedUpComingFlights(self,userID):
        query="SELECT `FlightNumber`, `DepartureTime`, `ArrivalTime`, `Origin`, `Dest`,`ConfirmationNumber`, `Price`, `StartDate`, `EndDate`, `Title` FROM UpcomingFlights WHERE UserID=%s AND DepartureTime > NOW() AND Active=1"
        self.cur.execute(query,(userID,))
        savedUpComingFlights={}
        for flightNumber,departureTime,arrivalTime,origin,dest, confirmationNumber,price,startDate,endDate,title in self.cur:
            flight=Flight(title=title,confirmationNumber=confirmationNumber, departureTime=departureTime,arrivalTime=arrivalTime,origin=origin,dest=dest,flightNumber=flightNumber,price=price, startDate=startDate,endDate=endDate)
            savedUpComingFlights[flight.getIdentifier()]=flight
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

