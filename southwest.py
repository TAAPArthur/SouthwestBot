import southwestScraper
from southwestRecords import Records
import sys

def run(users=None, loadCache=True, checkForNewPurchases=False, checkin=False, scan=False):
    database = Records()
    if not users:
        users = database.getUsers()

    bot = southwestScraper.SouthwestScraper(database, loadCache)
    for user in users:
        bot.setUser(user)
        bot.run(database.getSavedUpcomingFlights(user.id),
                checkForNewPurchases=checkForNewPurchases, checkin=checkin, scan=scan)
    bot.close()


if __name__ == "__main__":
    if len(sys.argv) == 4 or len(sys.argv) == 5:
        bot = southwestScraper.SouthwestScraper()
        bot.checkin(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) == 5 else None)
    else:
        if len(sys.argv) == 1:
            run(checkForNewPurchases=True, checkin=True, scan=True)
        else:
            if sys.argv[1] == "update":
                run(checkForNewPurchases=True, checkin=False, scan=False)
            elif sys.argv[1] == "check":
                run(checkForNewPurchases=False, checkin=True, scan=False)
