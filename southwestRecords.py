import mysql.connector
from datetime import datetime, date, timedelta
from southwestObjects import Flight, User, ScannedFlight


class Records:

    def __init__(self):
        self.conn = mysql.connector.connect(user='southwest', database='Southwest')
        self.cur = self.conn.cursor(buffered=True)

    def setUser(self, user):
        query = "REPLACE INTO Users VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cur.execute(query, user.getTuple())

    def getUser(self, chatID):
        query = "SELECT  Users.ID, `Username`, `Password`, `FirstName`, `LastName`, `TelegramChatID`, `StartDateDefaultDelta`, `EndDateDefaultDelta`, `PriceDelta`, `MinPrice` FROM `Users` WHERE TelegramChatID=%s LIMIT 1"
        self.cur.execute(query, (chatID,))
        for row in self.cur:
            return self._createUser(row)

    def getUsers(self):
        query = "SELECT  Users.ID, `Username`, `Password`, `FirstName`, `LastName`, `TelegramChatID`, `StartDateDefaultDelta`, `EndDateDefaultDelta`, `PriceDelta`, `MinPrice` FROM `Users` "
        self.cur.execute(query)
        users = []
        for row in self.cur:
            users.append(self._createUser(row))
        return users

    def _createUser(self, args):
        userID, username, password, firstName, lastName, chatID, defaultDeltaStart, defaultDeltaEnd, priceDelta, minPrice = args
        return User(userID, username, password, firstName, lastName, chatID, defaultDeltaStart, defaultDeltaEnd, priceDelta, minPrice)

    def setSavedUpcomingFlights(self, userID, flights):
        query = "UPDATE UpcomingFlights SET `Active`=2 WHERE UserID=%s AND DepartureTime > NOW() AND Active=1"
        self.cur.execute(query, (userID,))

        for flight in flights:
            self.saveUpcomingFlight(userID, flight)
        query = "UPDATE UpcomingFlights SET `Active`=0 WHERE UserID=%s AND Active=2"
        self.cur.execute(query, (userID,))

    def updatePriceOfUpComingFlights(self, userID, flight):
        query = "UPDATE UpcomingFlights SET `Price`=%s WHERE UserID=%s AND DepartureTime > NOW() AND Active=1 AND FlightNumber=%s AND DepartureTime=%s"
        self.cur.execute(query, (userID, flight.flightNumber, flight.departureTime.strftime("%Y-%m-%d %H:%M:%S")))

    def getSavedUpcomingFlights(self, userID):
        query = "SELECT `FlightNumber`, `DepartureTime`, `ArrivalTime`, `Origin`, `Dest`,`ConfirmationNumber`, `Price`, `StartDate`, `EndDate`, `Title` FROM UpcomingFlights WHERE UserID=%s AND DepartureTime > NOW() AND Active=1"
        self.cur.execute(query, (userID,))
        savedUpComingFlights = {}
        for flightNumber, departureTime, arrivalTime, origin, dest, confirmationNumber, price, startDate, endDate, title in self.cur:
            flight = Flight(title=title, confirmationNumber=confirmationNumber, departureTime=departureTime, arrivalTime=arrivalTime,
                            origin=origin, dest=dest, flightNumber=flightNumber, price=price, startDate=startDate, endDate=endDate)
            savedUpComingFlights[flight] = flight
        return savedUpComingFlights

    def saveUpcomingFlight(self, userID, flight):
        query = "REPLACE INTO `UpcomingFlights` (`UserID`, `ConfirmationNumber`, `FlightNumber`, `DepartureTime`, `ArrivalTime`, `Title`, `Origin`, `Dest`, `StartDate`, `EndDate`, `Price`, `Active` ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)"
        self.cur.execute(query, (userID, flight.confirmationNumber, flight.flightNumber, flight.departureTime.strftime("%Y-%m-%d %H:%M:%S"),
                                 flight.arrivalTime.strftime("%Y-%m-%d %H:%M:%S"), flight.title, flight.origin, flight.dest, flight.startDate, flight.endDate, flight.price))

    def saveCheapFlights(self, cheaperFlights):
        query = "REPLACE INTO `CheapFlights`(`DepartureTime`, `FlightNumber`, `Price` ) VALUES (%s,%s,%s)"
        for flight in cheaperFlights:
            self.cur.execute(query, (flight.departureTime, flight.flightNumber, flight.price))

    def getCheapFlights(self):
        query = "SELECT  DepartureTime, `FlightNumber`, `Price` FROM CheapFlights WHERE DepartureTime > NOW()"
        self.cur.execute(query)
        cheaperFlights = {}
        for departureTime, flightNumber, price in self.cur:
            cheaperFlights[Flight(flightNumber, departureTime=departureTime, arrivalTime=departureTime)] = price
        return cheaperFlights

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()

    @staticmethod
    def convertToLocalTime(date, airport):
        return date+timedelta(hours=Records.getOffset(date, airport))

    @staticmethod
    def getOffset(date, airport):
        if airport == "BOS":
            return -1
        elif airport == "SOF":
            return +2
        else:
            return 0
