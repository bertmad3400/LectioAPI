import re

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
