# For removing weird characthers that sometimes exist in text scraped from the internet
import unicodedata

# For iterating over parts of list
import itertools

from urllib.parse import urlparse, parse_qs

import re

showAllEventTargetPattern = re.compile(r's\$m\$Content\$Content\$threadGV\$ctl.*?(?=")')
beskedIDPattern = re.compile(r"(?<='__Page',').*?(?=')")

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
        try:
            ASPData[name] = pageSoup.find("input", {"name":name}).get("value")
        except AttributeError:
            ASPData[name] = ""

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

def extractBeskederShowAllEventTarget(pageSoup):
    try:
        pageNumberSoup = pageSoup.select("table#s_m_Content_Content_threadGV_ctl00 tbody tr.paging")[0]
    except:
        return None

    javascriptText = pageNumberSoup.find_all("td")[-1].find("a").get("href")

    return showAllEventTargetPattern.search(javascriptText).group()

def extractBeskeder(pageSoup):
    beskederSoup = pageSoup.select("table#s_m_Content_Content_threadGV_ctl00 tbody:first-child")[0]

    for element in beskederSoup.select("tr.paging"):
        element.decompose()

    titleSoup = beskederSoup.find_all("tr")[0]

    titles = []

    for row in itertools.islice(titleSoup.find_all("th"), 3, 7):
        titles.append(cleanText(row.text))

    titles.extend(["Vedhæftet?", "beskedID"])

    titleSoup.decompose()

    details = []

    for collumn in beskederSoup.find_all("tr"):
        details.append([])
        for row in itertools.islice(collumn.find_all("td"), 3, 7):
            details[-1].append(cleanText(row.text))

        details[-1].append("Ja" if collumn.find_all("td")[3].select('img[src*="/lectio/img/doc.gif"]') else "Nej")

        details[-1].append(beskedIDPattern.search(collumn.find_all("td")[3].select_one("a[onclick]").get("onclick")).group())

    return [{titles[i]:detail for i,detail in enumerate(detailList)} for detailList in details]
