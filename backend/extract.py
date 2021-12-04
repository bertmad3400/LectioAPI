from urllib.parse import urlparse, parse_qs

import re

# Function for extracting the elevid from any page where the user is logged in
def getElevID(pageSoup):
    rootURL = pageSoup.find("meta", {"name" : "msapplication-starturl"}).get("content")

    parsedURL = urlparse(rootURL)

    return parse_qs(parsedURL.query)['elevid'][0]

def extractASPData(pageSoup, eventTarget):
    ASPData = {"__EVENTTARGET" : eventTarget}

    for name in ["__VIEWSTATEX", "__EVENTVALIDATION", "__EVENTARGUMENT", "__SCROLLPOSITION", "__VIEWSTATEY_KEY", "__VIEWSTATE", "masterfootervalue"]:
        ASPData[name] = pageSoup.find("input", {"name":name}).get("value")

    return ASPData

def extractGymnasiumList(pageSoup):
    gymnasiumList = {}

    gymnasiumNumberPattern = re.compile("(?<=\/lectio\/)\d*(?=\/default\.aspx)")

    for element in pageSoup.find("div", {"id" : "schoolsdiv"}):
        try:
            gymnasiumNumber = int(gymnasiumNumberPattern.search(element.find("a").get('href')).group())
            gymnasiumList[gymnasiumNumber] = element.string
        except:
            continue

    return gymnasiumList
