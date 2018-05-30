#!/usr/bin/env python3

import sys
import time

import logging
from datetime import datetime, timedelta
import threading

from southwestObjects import Flight, User, ScannedFlight, setCheckinTimer
from southwestRecords import Records
from southwest import run




from telegram.ext import Updater
from telegram.ext import CommandHandler
import telegram
#logging.basicConfig(level=logging.ERROR,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


#TOKEN = open("token", "r").read().strip()
lock = threading.Lock()
LAST_SCAN = None
INTERVAL = timedelta(minutes=10)
USER_INTERVAL = timedelta(days=1)
USER_HISTORY = {}

class SouthwestMessenger:
    def __init__(self,token):
        self.token=token
    def start(self,bot, update):
        """
        Initializes the bot. Only needs to be run once
        """
        bot.sendMessage(chat_id=update.message.chat_id, text="Initlization complete.")


    def id(self,bot, update):
        """
        Outputs chatID
        """
        self.update.message.reply_text(update.message.chat_id)


    def at(self,bot, update, args):
        """
        /at firstName,lastName,confirmationNumber,time
        set a timer to checkin at time
        """
        if len(args) != 4:
            self.commandHelp(bot, update, "at")
            return
        firstName, lastName, confirmationNumber, time = args
        exitCode = setCheckinTimer(confirmationNumber, firstName, lastName, time)
        self.update.message.reply_text("%s %s will check in for flight %s at %s exitCode:%s" %
                                  (firstName, lastName, confirmationNumber, time, exitCode))


    def whoami(self,bot, update):
        """
        outputs user info
        """
        print("whoami")
        user = self.getUser(update)
        if user:
            self.update.message.reply_text(user.whoami())


    def setProperty(self,bot, update, args):
        """
        /set name property [name property ...]
        Sets user property
        """
        print(len(args))
        if len(args) < 2:
            self.commandHelp(bot, update, "set")
        else:
            user = self.getUser(update)
            if user:
                for i in range(0, len(args), 2):
                    if i+1 < len(args):
                        setattr(user, args[i], args[i+1])
                self.setUser(user)
                self.update.message.reply_text(user.whoami())


    def scan(self,bot, update, args):
        """
        Scans for a decrease in price value
        """
        with lock:
            user = self.getUser(update)

            if user and canScan(user):
                loadCache = len(args) != 0 and args[0] != "false"
                run([user], loadCache, scan=True)
                self.endScan(user)

            self.update.message.reply_text("scan complete")


    def update(self,bot, update):
        """
        Queries southwest for any changes to your upcoming flights. Then scans for any decrease in price
        """
        with lock:
            user = self.getUser(update)

            if user and canScan(user):
                run([user], loadCache=False, checkForNewPurchases=True, scan=True)
                self.endScan(user)
                self.update.message.reply_text("Update complete")


    def setFlight(self,bot, update, args):
        """
        Set Flight metadata: index,price, startOffset, endOffset
        index- index of the flight as reported by listFlights
        price- the amount you bought the flight for so we only send you cheaper flights
        startOffset- days before the flight to start scaning
        endOffset- days after the flight to start scaning
        """
        user = self.getUser(update)
        if user:
            r = Records()

            flight = list(r.getSavedUpcomingFlights(user.getID()).keys())[int(args[0])]
            flight.price = int(args[1])
            if len(args) > 2:
                flight.startDate = int(args[2])
                if len(args) > 3:
                    flight.endDate = int(args[3])
            r.saveUpcomingFlight(user.getID(), flight)
            r.commit()
            r.close()
            self.update.message.reply_text(str(flight))


    def listFlights(self,bot, update):
        """
        List all known upcoming flights. If you don't see your flight try running update
        If there is info we can't get like price of the flight, you can mananly set it using /setFlight
        """
        user = getUser(update)
        if user:
            r = Records()
            message = "\n".join(map(str, r.getSavedUpcomingFlights(user.getID())))
            r.commit()
            r.close()
            update.message.reply_text(message)


    def commandHelp(self,bot, update, args):
        """
        Displays help
        """

        if len(args) == 0:
            message = ""
            for handler in handlers:
                message += self.getDocStringMessageHandler(handler)
            self.update.message.reply_text(message)
        else:
            if isinstance(args, list):
                args = args[0]
            handler = getHandlerByCommand(args)
            self.update.message.reply_text("Message not found" if handler == None else self.getDocStringMessageHandler(handler))


    def canScan(self,user):
        if user in USER_HISTORY and datetime.now()-USER_HISTORY[user] < USER_INTERVAL:
            self.update.message.reply_text("You can only scan once per 24 hour period. Try again in %s ",
                                      str(datetime.now()-USER_HISTORY[user]))
            return False
        return True


    def endScan(self,user):
        global LAST_SCAN
        LAST_SCAN = USER_HISTORY[user] = datetime.now()


    def getUser(self,update):
        r = Records()
        user = r.getUser(update.message.chat_id)
        r.close()
        if not user:
            self.update.message.reply_text("User not found")
        return user


    def setUser(self,user):
        r = Records()
        r.setUser(user)
        r.close()


    def getHandlerByCommand(self,command):
        for handler in handlers:
            if command in handler.command:
                return handler


    def getDocStringMessageHandler(self,handler):
        return "%s - %s \n" % (str(handler.command) if len(handler.command) > 1 else handler.command[0], handler.callback.__doc__)


    def sendMessage(self,message, chatID):
        bot = telegram.Bot(token=self.token)
        bot.send_message(chat_id=chatID, text=message)


if __name__ == "__main__":
    
    #messenger=SouthwestMessenger(input("Please enter token"));
    messenger=SouthwestMessenger(open("token", "r").read().strip());
    
    if len(sys.argv) == 3:
        messenger.sendMessage(chatID=sys.argv[2], message=sys.argv[1])
    else:
        print("Starting chat bot")
        updater = Updater(token=self.token)
        dispatcher = updater.dispatcher
        handlers = [CommandHandler('start', messenger.start), CommandHandler('at', messenger.at, pass_args=True), CommandHandler('id', messenger.id),
                    CommandHandler('whoami', messenger.whoami), CommandHandler('set', messenger.setProperty, pass_args=True), CommandHandler('help', messenger.commandHelp, pass_args=True), CommandHandler('scan', messenger.scan, pass_args=True), CommandHandler(
                        'update', messenger.update), CommandHandler(['setflight', 'setFlight'], messenger.setFlight, pass_args=True), CommandHandler(['getflights', 'getFlights', 'list'], messenger.listFlights)
                    ]
        for handler in handlers:
            dispatcher.add_handler(handler)
        updater.start_polling()
        updater.idle()
