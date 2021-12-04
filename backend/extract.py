# For removing weird characthers that sometimes exist in text scraped from the internet
import unicodedata

from urllib.parse import urlparse, parse_qs

import re

def cleanText(text):
    return unicodedata.normalize("NFKD", text.replace("\t", "").replace("\n\n", "\n").strip("\n"))

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

    titles = [cleanText(element.text) for element in titlesSoup.find_all("th")]

    titles.append("Link")

    titlesSoup.decompose()

    details = []

    for collumn in opgaveSoup.find_all("tr"):
        details.append([cleanText(element.text) for element in collumn.find_all("td")])
        details[-1].append(f'https://lectio.dk{collumn.find("a").get("href")}')

    return [{titles[i]:detail for i,detail in enumerate(detailList)} for detailList in details]

def extractLektier(pageSoup):
    lektierSoup = pageSoup.select("div#s_m_Content_Content_contentPnl table.ls-table-layout1:first-child")[0]

    titles = [element.text for element in lektierSoup.select("thead tr:first-child")[0].find_all("th")]

    titles.extend(["Time-link", "Lektie-link"])

    details = []

    for collumn in lektierSoup.find("tbody").find_all("tr"):
        details.append([cleanText(collumn.find("th").text)])
        details[-1].extend([ cleanText(element.text) for element in collumn.find_all("td")])

        links = collumn.find_all("a")
        details[-1].append(f"https://lectio.dk{links[1].get('href')}")

        try:
            details[-1].append(f"https://lectio.dk{links[2].get('href')}")
        except IndexError:
            details[-1].append("")

    return [{titles[i]:detail for i,detail in enumerate(detailList)} for detailList in details]
