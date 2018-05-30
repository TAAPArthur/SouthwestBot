# SouthwestBot
Scan Southwest Airlines for a decrease in price

## Depends
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot): pip install python-telegram-bot --upgrade

[python-mysql-connector](https://dev.mysql.com/downloads/connector/python/): pip install mysql-connector

## Recommend cron options
0 1 * * * southwest-bot scan
@reboot southwest-bot listen
