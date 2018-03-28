#!/usr/bin/python3
import re
import sys
import time
import os

from datetime import datetime, date, timedelta
import traceback
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import _find_element
from selenium.webdriver.firefox.options import Options

from southwestRecords import Records
from southwestObjects import Flight, User, ScannedFlight
import southwestMessenger as SM

TIMEZONE = "America/Chicago"
HEADLESS=True

configDir=os.path.expanduser("~/.config/Southwest/")

class SouthwestBot:
    loginPage = "https://www.southwest.com/flight/login"
    accountPage = "https://www.southwest.com/myaccount"
    checkinPage = "https://www.southwest.com/air/check-in/index.html"
    flightsPage = "https://www.southwest.com/flight/"
    flightSelectionPage = "https://www.southwest.com/flight/select-flight.html?newDepartDate=%d-%d&newReturnDate="
    timeout = 20

    def __init__(self, database=None, loadCache=False):
        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
        self.driver = webdriver.Firefox(log_path=configDir+"geckodriver.log", firefox_options=options)
        self.driver.implicitly_wait(self.timeout)
        self.setUser(None)
        self.database = database
        self.cache = database.getCheapFlights() if loadCache else {}

    def setUser(self, user):
        self.user = user
        if user != None:
            self.output("setting user:", user)

    def message(self, message, id=None):
        if id == None:
            id = self.user.chatID
        if len(message) > 1 and id:
            SM.sendMessage(message, id)

    def output(self, *message):
        time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")+":"
        formattedMessage = str(message[0])
        for i in range(1, len(message)):
            formattedMessage += str(message[i])
        print(time, formattedMessage, flush=True)

    def screenshot(self, fileName="screenshot.png"):
        path = configDir+str(fileName)
        self.output("saving screen shot to ", path)
        self.driver.save_screenshot(path)

    def commit(self):
        self.database.commit()

    def close(self):
        self.database.close()

    def login(self):
        self.driver.get(self.loginPage)
        self.waitForElementToLoad("loyaltyLoginForm")
        self.driver.find_element_by_id("accountCredential").send_keys(self.user.username)
        self.driver.find_element_by_id("accountPassword").send_keys(self.user.password)
        self.driver.find_element_by_id("submit").click()
        self.output("logged in")
        self.output(self.driver.current_url)

    def checkin(self, confirmationNumber, firstName, lastName, id=None):
        self.driver.get(self.checkinPage)

        self.output("attemting to checking for %s %s (%s)" % (firstName, lastName, confirmationNumber))
        self.driver.find_element_by_id("confirmationNumber").clear()
        self.driver.find_element_by_id("passengerFirstName").clear()
        self.driver.find_element_by_id("passengerLastName").clear()
        self.driver.find_element_by_id("confirmationNumber").send_keys(confirmationNumber)
        self.driver.find_element_by_id("passengerFirstName").send_keys(firstName)
        self.driver.find_element_by_id("passengerLastName").send_keys(lastName)
        self.driver.find_element_by_id("form-mixin--submit-button").click()
        
        self.driver.find_element_by_class_name("air-check-in-review-results--check-in-button").click()
        self.screenshot();
        if self.driver.current_url != self.checkinPage:
            if id:
                self.message("checked in for %s %s (%s)" % (firstName, lastName, confirmationNumber), id)
        

    def waitForElementToLoad(self, id):
        element_present = EC.presence_of_element_located((By.ID, id))
        WebDriverWait(self.driver, self.timeout).until(element_present)

    def waitForElementToLoadByClass(self, clazz):
        element_present = EC.presence_of_element_located((By.CLASS_NAME, clazz))
        WebDriverWait(self.driver, self.timeout).until(element_present)

    def waitForElementToToBeClickableByClass(self, clazz):
        element_present = EC.element_to_be_clickable((By.CLASS_NAME, clazz))
        return WebDriverWait(self.driver, self.timeout).until(element_present)

    def waitForElementToHaveTextByClass(self, clazz):
        class text_to_be_present_in_element(object):
            """ An expectation for checking if the given text is present in the
            specified element.
            locator, text
            """

            def __init__(self, locator):
                self.locator = locator

            def __call__(self, driver):
                try:
                    return _find_element(driver, self.locator).text
                except StaleElementReferenceException:
                    return False
        element_present = text_to_be_present_in_element((By.CLASS_NAME, clazz))
        return WebDriverWait(self.driver, self.timeout).until(element_present)

    def getRecentFlights(self, savedUpComingFlights):

        tripLinks = []
        flights = []
        i = 0
        while True:
            tripElements = self.driver.find_elements_by_class_name("upcoming-trip-details-list-link")
            for tripElement in tripElements:
                tripLinks.append(tripElement.get_attribute("href"))
            nextButton = self.driver.find_element_by_class_name(
                "js-functional-bar-upcoming").find_element_by_class_name("js-right-arrow")
            if nextButton.get_attribute("disabled"):
                break
            else:
                self.waitForElementToToBeClickableByClass("js-right-arrow")
                nextButton.click()
                time.sleep(1)
            i += 1
            if i == 60:
                self.saveScreenshot("getRecentFlights.png")
                self.output("could not get recent flights")
                return[]
        for link in tripLinks:
            self.driver.get(link)
            self.output(link)

            confirmationNumber = self.waitForElementToHaveTextByClass("upcoming-details--confirmation-number")
            assert confirmationNumber != ""
            title = self.driver.find_element_by_class_name("upcoming-details--title").text
            rawDate = self.driver.find_elements_by_class_name("flight-details--date")

            firstRow = self.driver.find_elements_by_class_name("flight-details--first-row")
            lastRow = self.driver.find_elements_by_class_name("flight-details--row-last-child")
            assert len(rawDate) == len(firstRow)
            for i in range(len(rawDate)):
                date = rawDate[i].text.strip()
                assert date != ""

                startTime = firstRow[i].find_element_by_class_name("flight-details--trip-time").text.strip()
                endTime = lastRow[i].find_element_by_class_name("flight-details--trip-time").text.strip()
                origin = firstRow[i].find_element_by_class_name("flight-details--city").text
                dest = lastRow[i].find_element_by_class_name("flight-details--city").text
                departureTime = datetime.strptime(date+" "+startTime, "%m/%d/%y %I:%M%p")
                arrivalTime = datetime.strptime(date+" "+endTime, "%m/%d/%y %I:%M%p")
                flightNumber = int(firstRow[i].find_element_by_class_name("flight-details--flight-number").text)
                flight = Flight(title=title, confirmationNumber=confirmationNumber, departureTime=departureTime, arrivalTime=arrivalTime,
                                origin=origin, dest=dest, flightNumber=flightNumber, startDate=self.user.defaultDeltaStart, endDate=self.user.defaultDeltaEnd)

                if flight in savedUpComingFlights:
                    flight.copyMetadata(savedUpComingFlights[flight], self.user)

                flights.append(flight)

        return flights

    def getCheaperFlights(self, flight):
        def scanFlights(date, flight, newFlight, cheaperFlights):

            self.driver.find_element_by_class_name("bugTableRow")
            rows = self.driver.find_elements_by_class_name("bugTableRow")
            assert len(rows) != 0

            reducedPriceOnFlight = False
            for row in rows:
                prices = row.find_elements_by_class_name("price_column")
                if len(prices) < 3 or prices[2].text.strip() == "Sold Out" or prices[2].text.strip() == "Unavailable":
                    continue
                try:
                    price = int(prices[2].text.strip()[1:])
                except:
                    self.output("could not parse %s as int" % prices[2].text)
                    continue
                if price > self.user.minPrice or flight.price and flight.price-price < self.user.priceDelta:
                    continue
                startTime = row.find_element_by_class_name("depart_column").text
                endTime = row.find_element_by_class_name("arrive_column").text[:8].strip()
                start = datetime.combine(date, datetime.time(datetime.strptime(startTime, "%I:%M %p")))
                end = datetime.combine(date, datetime.time(datetime.strptime(endTime, "%I:%M %p")))

                flightNumber = int(row.find_element_by_class_name("swa_text_flightNumber").text.split("\n")[0])
                routing = row.find_element_by_class_name("routing_column").text

                cheaperFlight = ScannedFlight(flightNumber, start, end, price, routing, flight)
                if cheaperFlight == flight:
                    if not flight.price:
                        flight.price = price
                    elif price < flight.price:
                        reducedPriceOnFlight = price
                    else:
                        continue
                    self.output("setting flight price: ", flight)
                    for c in list(cheaperFlights):
                        if c.price > flight.price:
                            cheaperFlights.remove(c)
                    continue
                if cheaperFlight in self.cache:
                    if self.cache[cheaperFlight] >= cheaperFlight.price:
                        self.cache[cheaperFlight] = cheaperFlight.price
                        if self.cache[cheaperFlight] > cheaperFlight.price:
                            self.database.saveCheapFlights([cheaperFlight])
                        if not newFlight:
                            continue

                cheaperFlights.append(cheaperFlight)
            return reducedPriceOnFlight

        self.driver.get(self.flightsPage)
        time.sleep(1)
        self.driver.find_element_by_id("oneWay").click()
        time.sleep(1)
        dest = self.driver.find_element_by_id("destinationAirport_displayed")
        origin = self.driver.find_element_by_id("originAirport_displayed")
        departDate = self.driver.find_element_by_id("outboundDate")
        dest.clear()
        origin.clear()
        departDate.clear()
        dest.send_keys(flight.dest)
        time.sleep(1)
        origin.send_keys(flight.origin)
        time.sleep(1)
        departDate.send_keys(flight.getDateString())
        time.sleep(1)
        self.driver.find_element_by_id("submitButton").click()

        newFlight = flight.price == None
        cheaperFlights = []
        currentFlightReducedPrice = scanFlights(flight.getDate(), flight, newFlight, cheaperFlights)
        for date in flight.getDates()[1:]:
            if date > datetime.date(datetime.now()):
                time.sleep(5)
                self.driver.get(self.flightSelectionPage % (date.month, date.day))

                scanFlights(date, flight, newFlight, cheaperFlights)
        return cheaperFlights, currentFlightReducedPrice

    def notifyUserOfCheaperFlights(self, flight):
        previousPrice = flight.price
        cheaperFlights, currentFlightReducedPrice = self.getCheaperFlights(flight)
        cheaperFlights.sort()
        cheaperFlights = cheaperFlights[:10]
        if self.database:
            self.database.saveCheapFlights(cheaperFlights)
            if previousPrice == None:
                if flight.price == None:
                    flight.price = 0
                self.database.saveUpcomingFlight(self.user.getID(), flight)
        if len(cheaperFlights) > 0:
            message = "In relation to %s\n %d cheaperFlights found" % (str(flight), len(cheaperFlights))
            for cheaperFlight in cheaperFlights:
                message += (str(cheaperFlight)+"\n")
            self.message(message)
        if currentFlightReducedPrice:
            if self.database:
                self.database.updatePriceOfUpComingFlights(self.user.getID(), flight)
            self.message("Your current flight's price has been reduced by $%d to $%d; Flight Info %s" %
                         (previousPrice-currentFlightReducedPrice, currentFlightReducedPrice, str(flight)))

    def run(self, savedUpComingFlights, checkForNewPurchases=False, checkin=False, scan=False):
        try:
            self.login()

            if checkForNewPurchases:
                self.output("Checking for new purchases")
                flights = self.getRecentFlights(savedUpComingFlights)
                print(flights)
                print(flights[0])
                if self.database:
                    self.database.setSavedUpcomingFlights(self.user.getID(), flights)
            else:
                flights = savedUpComingFlights

            self.output("found %d flights" % len(flights))

            if checkin:
                self.output("Attempting to set checkin timer")
                for flight in flights:
                    if flight.shouldSetCheckinTimer(self.database):
                        self.output("Setting timer to check in for %s" % str(flight))
                        flight.setCheckinTimer(self.user)
                        SM.sendMessage("You have an upcoming flight %s" % str(flight), self.user.getChatID())
            if scan:
                self.output("Scanning")
                for flight in flights:
                    self.notifyUserOfCheaperFlights(flight)
            self.commit()

        except:
            self.output("Failed to run with %s " % self.user.username)
            self.screenshot("%s.png" % self.user.username)
            traceback.print_exc()
            # traceback.print_stack()


def run(users=None, loadCache=True, checkForNewPurchases=False, checkin=False, scan=False):
    database = Records()
    if not users:
        users = database.getUsers()

    bot = SouthwestBot(database, loadCache)
    for user in users:
        bot.setUser(user)
        bot.run(database.getSavedUpcomingFlights(user.id),
                checkForNewPurchases=checkForNewPurchases, checkin=checkin, scan=scan)
    bot.close()


if __name__ == "__main__":
    if len(sys.argv) == 4 or len(sys.argv) == 5:
        bot = SouthwestBot()
        bot.checkin(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) == 5 else None)
    else:
        if len(sys.argv) == 1:
            run(checkForNewPurchases=False, checkin=True, scan=True)
        else:
            if sys.argv[1] == "update":
                run(checkForNewPurchases=True, checkin=False, scan=False)
            elif sys.argv[1] == "check":
                run(checkForNewPurchases=False, checkin=True, scan=False)
