#!/usr/bin/env python3
from telegram.ext import Updater
from telegram.ext import CommandHandler
import telegram
import sys
import southwestRecords import Records,Flight,User,ScannedFlight,setCheckinTimer
from token import TOKEN


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Initlization complete. your chat id is %d" % update.message.chat_id)
def id(bot, update):
    update.message.reply_text(update.message.chat_id)
def at(bot,update):
    firstName,lastName,confirmationNumber,time=tuple(update.message.text.strip()[3:].strip().split(" "))
    exitCode=setCheckinTimer(confirmationNumber,firstName,lastName,time)
    update.message.reply_text("%s %s will check in for flight %s at %s exitCode:%s" %(firstName,lastName,confirmationNumber,time,exitCode))
    
def sendMessage(message,id):
    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=id,text=message)

if __name__ == "__main__":
    if len(sys.argv)==3:
        sendMessage(sys.argv[1],sys.argv[2])
    else:
        print("Starting bot")
        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher
        handlers=[CommandHandler('start', start),CommandHandler('at', at),CommandHandler('id', id)]
        for handler in handlers:
            dispatcher.add_handler(handler)
        updater.start_polling()
        updater.idle()

