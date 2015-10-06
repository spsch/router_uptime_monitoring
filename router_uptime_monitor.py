#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup

from time import sleep
import datetime
import os
import re
import subprocess
import urllib2

""" Returns the timestring obtained from parsing the html provided by the router

                @throws if the html page cannot be retrieved from the router
"""
def getUptimeFromRouter():

    passwordManager = urllib2.HTTPPasswordMgrWithDefaultRealm()

    topLevelUrl = "http://192.168.1.1"
    loginLevelUrl = "http://192.168.1.1/ui/1.0.99.161129/dynamic/login.html"
    passwordManager.add_password(None, loginLevelUrl, "admin", "CashplayAdmin12")
    handler = urllib2.HTTPBasicAuthHandler(passwordManager)
    opener = urllib2.build_opener(handler)
    page = opener.open(topLevelUrl + "/ui/1.0.99.161129/dynamic/home.html")
    opener.open(topLevelUrl + "/ui/dynamic/login.html")

    soup = BeautifulSoup(page)

    uptimeString = ""
    for elem in soup('td', text="Connected time so far"):
        uptimeString = elem.parent.nextSibling.nextSibling.next

    return uptimeString

def checkRouterForFailure(uptimeString):
    if uptimeString == "":
        print "Uptime string from router was empty, cannot be sure if there was downtime so waiting till next time"
        return

    longFormRegex = "^([0-9]+) days?, ([0-9]+) hours?"
    shortFormRegex = "^([0-9][0-9]):([0-9][0-9]):([0-9][0-9])"
    previousUptimeStorage = "previousUptime.storage"
    resultsFile = "results.log"

    currUptime = datetime.timedelta()
    shortMatch = re.search(shortFormRegex, uptimeString)
    longMatch = re.search(longFormRegex, uptimeString)

    if shortMatch:
        parsedHours = int(shortMatch.group(1))
        parsedMinutes = int(shortMatch.group(2))
        parsedSeconds = int(shortMatch.group(3))
        currUptime = datetime.timedelta(hours = parsedHours, minutes = parsedMinutes, seconds = parsedSeconds)
        print "ShortMatch uptime: " + str(currUptime)

    elif longMatch:
        currUptime = datetime.timedelta( hours = (int(longMatch.group(1)) * 24) + int(longMatch.group(2)) )
        print "LongMatch uptime: " + str(currUptime)

    else:
        print "time string: " + uptimeString + " did not match either the short or long time format expected, waiting till next time"
        return

    # get the previous stored uptime
    previousUptime = datetime.timedelta(seconds=0)
    if os.path.exists(previousUptimeStorage):
        previousUptimeFile = open(previousUptimeStorage, "r")
        previousUptime = datetime.timedelta(seconds=int(previousUptimeFile.read()))
        print "PrevUptime: " + str(previousUptime)
        previousUptimeFile.close()

    # if we went backwards then we had a disconnection!
    if currUptime < previousUptime:
        resultsLog = open(resultsFile, "a")
        outputString = "Router lost internet connection!!\nUptime before failure was: " + str(previousUptime)
        print outputString
        resultsLog.write(outputString + "\n\n")
    else:
        print "Router has maintained it's connection since the last check, no downtime"

    # write out the previous uptime
    totalCurrUptimeSeconds = currUptime.seconds + (currUptime.days * 3600 * 24)
    open(previousUptimeStorage, "w").write(str(totalCurrUptimeSeconds))

while(1):
    try:
        uptimeString = getUptimeFromRouter()
        checkRouterForFailure(uptimeString)

    except Exception as e:
        print "Retrieval of uptime from router failed because: " + str(e)

    waitTime = 60
    print "Waiting " + str(waitTime) + " seconds until doing next check"
    sleep(waitTime)
