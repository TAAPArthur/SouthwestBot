from datetime import datetime, date, timedelta
from os import system


class Flight:
    def __init__(self, flightNumber, departureTime, arrivalTime, origin=None, dest=None, confirmationNumber=None, price=None, startDate=None, endDate=None, title=None):
        self.title = title
        self.confirmationNumber = confirmationNumber
        self.departureTime = departureTime
        self.arrivalTime = arrivalTime
        self.origin = origin
        self.dest = dest
        self.flightNumber = int(flightNumber)
        self.setMetadata(price, startDate, endDate)

    def copyMetadata(self, flight, user):
        price, startDate, endDate = flight.getMetdata()
        if startDate == None:
            startDate = user.defaultDeltaStart
        if endDate == None:
            endDate = user.defaultDeltaEnd
        self.setMetadata(price, startDate, endDate)

    def setMetadata(self, price, startDate, endDate):
        self.price = price
        self.startDate = startDate
        self.endDate = endDate

    def getMetdata(self):
        return self.price, self.startDate, self.endDate

    def getIdentifier(self):
        return self.flightNumber, self.departureTime

    def shouldSetCheckinTimer(self, database=None):
        return (database.convertToLocalTime(self.departureTime, self.origin)-datetime.now()).days == 1

    def setCheckinTimer(self, user):
        setCheckinTimer(self.confirmationNumber, user.firstName, user.lastName,
                        user.getChatID(), self.departureTime.strftime("%H%M"), self.origin)

    def __hash__(self):
        return hash(self.getIdentifier())

    def __eq__(self, other):
        return other.getIdentifier and other.getIdentifier() == self.getIdentifier()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.price < other.price

    def __str__(self):
        return "#%d %s-%s %s to %s ($%s) range: %s confirmation number: %s" % (self.flightNumber, self.departureTime.strftime("%b %d %y %H:%M"), self.arrivalTime.strftime("%H:%M"), self.origin, self.dest, self.price, self.getRangeString(), self.confirmationNumber)

    def getRangeString(self):
        if self.startDate or self.endDate:
            return "%s to %s" % (self.startDate, self.endDate)
        else:
            return "None"

    def getDate(self):
        return datetime.date(self.departureTime)

    def getDates(self):
        dateRange = list(range(-self.startDate, self.endDate))
        dateRange.sort(key=lambda x: abs(x))
        date = self.getDate()
        return list(map(lambda x: date-timedelta(x), dateRange))

    def getDateString(self):
        return self.departureTime.strftime("%m/%d/%Y")


class ScannedFlight(Flight):
    def __init__(self, flightNumber, departureTime, arrivalTime, price, routing, flight):
        super().__init__(flightNumber=flightNumber, departureTime=departureTime,
                         arrivalTime=arrivalTime, origin=flight.origin, dest=flight.dest, price=price)
        self.routing = routing.split("\n")[0].strip()

    def __str__(self):
        return super().__str__()+" $%d %s" % (self.price, self.routing)


class User:
    def __init__(self, userID, username, password, firstName, lastName, chatID, defaultDeltaStart=7, defaultDeltaEnd=7, priceDelta=5, minPrice=2000):
        self.id = int(userID)
        self.username = username
        self.password = password
        self.firstName = firstName
        self.lastName = lastName
        self.chatID = chatID
        self.defaultDeltaStart = defaultDeltaStart
        self.defaultDeltaEnd = defaultDeltaEnd
        self.priceDelta = float(priceDelta)
        self.minPrice = float(minPrice)

    def getID(self):
        return self.id

    def getChatID(self):
        return self.chatID

    def getTuple(self):
        return self.id, self.username, self.password, self.firstName, self.lastName, self.chatID, self.defaultDeltaStart, self.defaultDeltaEnd, self.priceDelta, self.minPrice

    def __str__(self):
        return self.username

    def whoami(self):
        return "username:%s password:%s firstName:%s lastName:%s defaultDeltaStart:%s defaultDeltaEnd:%s priceDelta:%s minPrice:%s" % (self.username, self.password, self.firstName, self.lastName, self.defaultDeltaStart, self.defaultDeltaEnd, self.priceDelta, self.minPrice)


def setCheckinTimer(confirmationNumber, firstName, lastName, userID, time, origin):
    print("southwest-bot set-checkin-timer \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" " %
          (confirmationNumber, firstName, lastName, userID, time, getTimezoneFromAirport(origin)))
    return system("southwest-bot set-checkin-timer \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" " % (confirmationNumber, firstName, lastName, userID, int(time), getTimezoneFromAirport(origin)))


def getTimezoneFromAirport(airport):
    with open("timezones.txt") as f:
        for line in f:
            if line.startswith(airport):
                return line[len(airport)+1:-1]
    return "America/Chicago"
