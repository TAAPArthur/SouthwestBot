#!/usr/bin/env python3
from telegram.ext import Updater
from telegram.ext import CommandHandler
import telegram
import sys

from southwestRecords import Records,Flight,User,ScannedFlight,setCheckinTimer

import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


TOKEN=open("token","r").read().strip()

def start(bot, update):
    """
    Initializes the bot. Only needs to be run once
    """
    bot.sendMessage(chat_id=update.message.chat_id, text="Initlization complete.")
def id(bot, update):
    """
    Outputs chatID
    """
    update.message.reply_text(update.message.chat_id)

def at(bot,update,args):
    """
    /at firstName,lastName,confirmationNumber,time
    set a timer to checkin at time
    """
    if len(args)!=4:
        commandHelp(bot,update,"at")
        return
    firstName,lastName,confirmationNumber,time=args
    exitCode=setCheckinTimer(confirmationNumber,firstName,lastName,time)
    update.message.reply_text("%s %s will check in for flight %s at %s exitCode:%s" %(firstName,lastName,confirmationNumber,time,exitCode))
    

def whoami(bot,update):
    """
    outputs user info
    """
    print("whoami")
    user=getUser(update)
    print(user)
    update.message.reply_text(user.whoami() if user else "User not found")
        

def setProperty(bot,update,args):
    """
    /set name property [name property ...]
    Sets user property
    """
    print(len(args))
    if len(args)<2:
        commandHelp(bot,update,"set")
    else:
        user=getUser(update)
        if user:
            for i in range(0,len(args),2):
                if i+1 < len(args):
                    setattr(user,args[i],args[i+1])
            setUser(user)
            update.message.reply_text(user.whoami())
        else:
            update.message.reply_text("user not found")
        

def commandHelp(bot,update,args):
    """
    Displays help
    """
    
    if len(args)==0:
        message=""
        for handler in handlers:
            message=getDocStringMessageHandler(handler)
        update.message.reply_text(message)
    else :
        if isinstance(args,list):
            args=args[0]
        handler=getHandlerByCommand(args)
        update.message.reply_text("Message not found" if handler==None else getDocStringMessageHandler(handler))


def getUser(update):
    r=Records()
    user=r.getUser(update.message.chat_id)
    r.close()
    return user
def setUser(user):
    r=Records()
    r.setUser(user)
    r.close()
def getHandlerByCommand(command):
    for handler in handlers:
        if command in handler.command:
            return handler
def getDocStringMessageHandler(handler):
    return "%s - %s \n" % (str(handler.command) if len(handler.command)>1 else handler.command[0],handler.callback.__doc__)
        
def sendMessage(message,id):
    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=id,text=message)

if __name__ == "__main__":
    if len(sys.argv)==3:
        sendMessage(sys.argv[1],sys.argv[2])
    else:
        print("Starting chat bot")
        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher
        handlers=[CommandHandler('start', start),CommandHandler('at', at,pass_args=True),CommandHandler('id', id),
        CommandHandler('whoami', whoami),CommandHandler('set', setProperty,pass_args=True),CommandHandler('help', commandHelp,pass_args=True)
        ]
        for handler in handlers:
            dispatcher.add_handler(handler)
        r=Records()
        updater.start_polling()
        updater.idle()

