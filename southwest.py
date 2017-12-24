#!/usr/bin/python3
import re
import sys
import time
from datetime import datetime,date,timedelta

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from southwestRecords import Records,Flight,User,ScannedFlight
from southwestMessenger import sendMessage


class SouthwestBot:
    loginPage="https://www.southwest.com/flight/login"
    accountPage="https://www.southwest.com/myaccount"
    checkinPage="https://www.southwest.com/air/check-in/index.html"
    flightsPage="https://www.southwest.com/flight/"
    flightSelectionPage="https://www.southwest.com/flight/select-flight.html?newDepartDate=%d-%d&newReturnDate="
    timeout=7
    
    
    
    def __init__(self,user=None,cache={}):
        self.driver = webdriver.PhantomJS(service_log_path="/dev/null",service_args=['--ssl-protocol=any'])
        self.driver.implicitly_wait(self.timeout)
        self.setUser(user)
        self.cache=cache
    def setUser(self,user):
        self.user=user
        if user!=None:
            self.output("setting user:",user)
    def login(self):
        self.driver.get(self.loginPage)
        self.waitForElementToLoad("loyaltyLoginForm")
        self.driver.find_element_by_id("accountCredential").send_keys(self.user.username)
        self.driver.find_element_by_id("accountPassword").send_keys(self.user.password)
        self.driver.find_element_by_id("submit").click()
        self.output("logged in")
        self.output(self.driver.current_url)
    def checkin(self,confirmationNumber,firstName,lastName,id=None):
        self.driver.get(self.checkinPage)
        
        self.output("attemting to checking for %s %s (%s)" % (firstName,lastName,confirmationNumber))
        i=0
        while True:
            self.driver.find_element_by_id("confirmationNumber").clear()
            self.driver.find_element_by_id("passengerFirstName").clear()
            self.driver.find_element_by_id("passengerLastName").clear()
            self.driver.find_element_by_id("confirmationNumber").send_keys(confirmationNumber)
            self.driver.find_element_by_id("passengerFirstName").send_keys(firstName)
            self.driver.find_element_by_id("passengerLastName").send_keys(lastName)
            self.driver.find_element_by_id("form-mixin--submit-button").click()
            if self.driver.current_url!=self.checkinPage:
                if id:
                    self.message("checked in to %s %s (%s)" % (firstName,lastName,confirmationNumber),id)
                break
            i+=1
            time.sleep(1)
            if i==60:
                self.output("could not checking")
                break
    def autoCheckIn(self,flights):
        for flight in flights:
            if flight.shouldSetCheckinTimer():
                flight.setCheckinTimer(self.user)
    def waitForElementToLoad(self,id):
        element_present = EC.presence_of_element_located((By.ID, id))
        WebDriverWait(self.driver, self.timeout).until(element_present)
    def waitForElementToLoadByClass(self,clazz):
        element_present = EC.presence_of_element_located((By.CLASS_NAME, clazz))
        WebDriverWait(self.driver, self.timeout).until(element_present)
        
    def waitForElementToToBeClickableByClass(self,clazz):
        element_present = EC.element_to_be_clickable((By.CLASS_NAME, clazz))
        return WebDriverWait(self.driver, self.timeout).until(element_present)
    
    def getRecentFlights(self,savedUpComingFlights):
        
        tripLinks=[]
        flights=[]
        while True:
            tripElements=self.driver.find_elements_by_class_name("upcoming-trip-details-list-link")
            for tripElement in tripElements:
                tripLinks.append(tripElement.get_attribute("href"))
            nextButton=self.driver.find_element_by_class_name("js-functional-bar-upcoming").find_element_by_class_name("js-right-arrow")
            if nextButton.get_attribute("disabled"):
                break
            else:
                self.waitForElementToToBeClickableByClass("js-right-arrow")
                nextButton.click()
                time.sleep(1)
        for link in tripLinks:
            self.driver.get(link)
            self.output(link)
            
            
            while True:
                confirmationNumber=self.driver.find_element_by_class_name("upcoming-details--confirmation-number").text
                if confirmationNumber != "":
                    break
                time.sleep(1)
            title=self.driver.find_element_by_class_name("upcoming-details--title").text
            rawDate=self.driver.find_elements_by_class_name("flight-details--date")
            
            
            firstRow=self.driver.find_elements_by_class_name("flight-details--first-row")
            lastRow=self.driver.find_elements_by_class_name("flight-details--row-last-child")
            assert len(rawDate)==len(firstRow)
            for i in range(len(rawDate)):
                while True:
                    date=rawDate[i].text.strip()
                    if date != "":
                        break
                    time.sleep(1)
                
                
                startTime=firstRow[i].find_element_by_class_name("flight-details--trip-time").text.strip()
                endTime=lastRow[i].find_element_by_class_name("flight-details--trip-time").text.strip()
                origin=firstRow[i].find_element_by_class_name("flight-details--city").text
                dest=lastRow[i].find_element_by_class_name("flight-details--city").text
                departureTime=datetime.strptime(date+" "+startTime,"%m/%d/%y %I:%M%p")
                arrivalTime=datetime.strptime(date+" "+endTime,"%m/%d/%y %I:%M%p")
                flightNumber=int(firstRow[i].find_element_by_class_name("flight-details--flight-number").text)
                flight=Flight(title=title,confirmationNumber=confirmationNumber, departureTime=departureTime,arrivalTime=arrivalTime,origin=origin,dest=dest,flightNumber=flightNumber, startDate=self.user.defaultDeltaStart,endDate=self.user.defaultDeltaEnd)         
                if flight in savedUpComingFlights:
                    price,startDate,endDate=savedUpComingFlights[flight]
                    if startDate==None:
                        startDate=self.user.defaultDeltaStart
                    if endDate==None:
                        endDate=self.user.defaultDeltaEnd
                        
                    flight.setMetadata(price,startDate,endDate)
                flights.append(flight)
                
        return flights

    def getCheaperFlights(self,flight):
        def scanFlights(date,flight,newFlight,cheaperFlights):
            while True:
                rows=self.driver.find_elements_by_class_name("bugTableRow")
                if len(rows)!=0:
                    break
                time.sleep(1)
                
            reducedPriceOnFlight=False
            for row in rows:
                prices=row.find_elements_by_class_name("price_column")
                if len(prices)<3 or prices[2].text.strip()=="Sold Out" or prices[2].text.strip()=="Unavailable":
                    continue
                try:
                    price=int(prices[2].text.strip()[1:])
                except:
                    self.output("could not parse %s as int" % prices[2].text)
                    continue
                if price > user.minPrice or flight.price and flight.price-price<user.priceDelta:
                    continue
                startTime=row.find_element_by_class_name("depart_column").text
                endTime=row.find_element_by_class_name("arrive_column").text[:8].strip()
                start=datetime.combine(date,datetime.time(datetime.strptime(startTime,"%I:%M %p")))
                end=datetime.combine(date,datetime.time(datetime.strptime(endTime,"%I:%M %p")))
                
                flightNumber=int(row.find_element_by_class_name("swa_text_flightNumber").text.split("\n")[0])
                routing=row.find_element_by_class_name("routing_column").text
                    
                cheaperFlight=ScannedFlight(flightNumber,start,end,price,routing,flight)
                if cheaperFlight == flight:
                    if not flight.price:
                        flight.price=price
                    elif price< flight.price:
                        reducedPriceOnFlight=price
                    else:
                        continue
                    self.output("setting flight price: ",flight)
                    for c in list(cheaperFlights):
                        if c.price > flight.price:
                            cheaperFlights.remove(c)
                    continue
                if cheaperFlight in self.cache:
                    if self.cache[cheaperFlight]>=cheaperFlight.price:
                        self.cache[cheaperFlight]=cheaperFlight.price
                        if self.cache[cheaperFlight]>cheaperFlight.price:
                            database.saveCheapFlights([cheaperFlight])
                        if not newFlight:
                            continue
                        
                cheaperFlights.append(cheaperFlight)
            return reducedPriceOnFlight
            
        self.driver.get(self.flightsPage)
        time.sleep(2)
        self.driver.find_element_by_id("oneWay").click()
        dest=self.driver.find_element_by_id("destinationAirport_displayed")
        origin=self.driver.find_element_by_id("originAirport_displayed")
        departDate=self.driver.find_element_by_id("outboundDate")
        
        dest.clear()
        origin.clear()
        departDate.clear()
        dest.send_keys(flight.dest)
        time.sleep(.5)
        origin.send_keys(flight.origin)
        time.sleep(.5)
        departDate.send_keys(flight.getDateString())
        time.sleep(.5)
        self.driver.find_element_by_id("submitButton").click()
        
        newFlight=flight.price==None
        cheaperFlights=[]
        currentFlightReducedPrice=scanFlights(flight.getDate(),flight,newFlight,cheaperFlights)
        for date in flight.getDates()[1:]:
            if date > datetime.date(datetime.now()):
                self.driver.get(self.flightSelectionPage % (date.month,date.day))
                scanFlights(date,flight,newFlight,cheaperFlights)
        return cheaperFlights,currentFlightReducedPrice
        
    

    def notifyUserOfCheaperFlights(self,flight):
        previousPrice=flight.price
        cheaperFlights,currentFlightReducedPrice=self.getCheaperFlights(flight)
        cheaperFlights.sort()
        cheaperFlights=cheaperFlights[:10]
        if database:
            database.saveCheapFlights(cheaperFlights)
            if previousPrice == None:
                if flight.price==None:
                    flight.price=0
                database.saveNewFlight(self.user.id,flight)
        message=""
        for cheaperFlight in cheaperFlights:
            message+=(str(cheaperFlight)+"\n")
        self.message(message)
        if currentFlightReducedPrice:
            self.message("Your current flight's price has been reduced by $%d to $%d; Flight Info %s" % (previousPrice-currentFlightReducedPrice, currentFlightReducedPrice,str(flight)))
        
    def message(self,message,id=None):
        if id ==None:
            id=self.user.chatID
        if len(message)>1 and id:
            sendMessage(message,id)
        
    def saveScreenshot(self,fileName="screenshot.png"):
        self.output("saving screen shot to ",fileName)
        self.driver.save_screenshot(fileName)
        

    def output(self,*message):
        
        time=datetime.now().strftime("%Y/%m/%d %H:%M:%S")+":"
        formattedMessage=str(message[0])
        for i in range(1,len(message)):
            formattedMessage+=str(message[i])
        print (time,formattedMessage, flush=True)
    
    def run(self,savedUpComingFlights):
        self.login()
        flights=self.getRecentFlights(savedUpComingFlights)
        #self.autoCheckIn(flights)
        for flight in flights:
            self.notifyUserOfCheaperFlights(flight)
            
if __name__ == "__main__":
    if len(sys.argv)==4:
        bot=SouthwestBot(None)
        bot.checkin(sys.argv[1],sys.argv[2],sys.argv[3])
    else:
        database=Records()
        
        users=database.getUsers()
                
        cache=database.getCheapFlights()
        bot=SouthwestBot(None,cache)
        for user in users:
            bot.setUser(user)
            bot.run(database.getSavedUpComingFlights(user.id))
            database.commit()
        database.close()
