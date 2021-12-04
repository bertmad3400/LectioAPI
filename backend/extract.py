# For removing weird characthers that sometimes exist in text scraped from the internet
import unicodedata

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

def extractOpgaver(pageSoup):
    opgaveSoup = pageSoup.select("table#s_m_Content_Content_ExerciseGV tbody:first-child")[0]

    titlesSoup = opgaveSoup.select("tr:first-child")[0]

    titles = [element.text for element in titlesSoup.find_all("th")]

    titlesSoup.decompose()

    details = []

    for collumn in opgaveSoup.find_all("tr"):
        details.append([unicodedata.normalize("NFKD", element.text.replace("\t", "").replace("\n", "")) for element in collumn.find_all("td")])

    return [{titles[i]:detail for i,detail in enumerate(detailList)} for detailList in details]
