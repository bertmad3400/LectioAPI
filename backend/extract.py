# For removing weird characthers that sometimes exist in text scraped from the internet
import unicodedata

# For iterating over parts of list
import itertools

# For parsing dates from skema
from datetime import datetime

from urllib.parse import urlparse, parse_qs

import re

# Used for creating deep copy of dict
import copy

showAllEventTargetPattern = re.compile(r's\$m\$Content\$Content\$threadGV\$ctl.*?(?=")')
beskedIDPattern = re.compile(r"(?<='__Page',').*?(?=')")
beskedPadPattern = re.compile(r"(?<=padding-left:)[0-9\.]*?(?=em)")

datePattern = re.compile(r"\d{1,2}\/\d{1,2}-\d{4}")
timePattern = re.compile(r"\d{2}:\d{2}")

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

def extractBeskedContent(beskedSoup, beskedDictsList):
    for besked in beskedSoup.find_all("li"):

        try:
            besked.get("style")
        except AttributeError:
            continue

        beskedPad = float(beskedPadPattern.search(besked.get("style")).group())

        newBeskedDict = {
                    "title" : cleanText(besked.find("h4").text),
                    "forfatter" : cleanText(besked.find("span").text),
                    "indhold" : cleanText(besked.find_all("div")[-1].text),
                    "pad" : str(beskedPad),
                    "replies" : []
                }

        if beskedPad > float(beskedDictsList[-1]["pad"]):
            beskedDictsList[-1]["replies"].append(newBeskedDict)
            besked.decompose()
            extractBeskedContent(beskedSoup, beskedDictsList[-1]["replies"])
        elif beskedPad == float(beskedDictsList[-1]["pad"]):
            beskedDictsList.append(newBeskedDict)
            besked.decompose()
        else:
            break

def extractBesked(pageSoup):
    beskedSoup = pageSoup.select_one("ul#s_m_Content_Content_ThreadList")

    beskeder = [{
            "title" : cleanText(pageSoup.select_one("table.ShowMessageRecipients td.textLeft").text),
            "Afsender" : cleanText(pageSoup.select("table.ShowMessageRecipients tbody tr:last-child table tbody tr:first-child td:last-child")[0].text),
            "Modtager" : cleanText(pageSoup.select("table.ShowMessageRecipients tbody tr:last-child table tbody tr:last-child td:last-child")[0].text),
            "pad" : "-1",
            "replies" : []
        }]

    extractBeskedContent(beskedSoup, beskeder)

    return beskeder

def extractSkema(pageSoup):
    skemaSoup = pageSoup.select_one("table#s_m_Content_Content_SkemaNyMedNavigation_skema_skematabel tbody")

    titleSoup = skemaSoup.select("tr.s2dayHeader td")
    # The first element is just empty, so remove that
    titleSoup.pop(0).decompose()

    titles = [cleanText(element.text) for element in titleSoup]

    informationHeaders = skemaSoup.select("td.s2infoHeader")
    # The first element is just empty, so remove that
    informationHeaders.pop(0).decompose()

    informations = []

    for header in informationHeaders:
        informations.append([cleanText(element.text) for element in header.select("a.s2skemabrik")])

    skemaDays = skemaSoup.select("div.s2skemabrikcontainer")
    # The first element is times (which we don't need), so remove that
    skemaDays.pop(0).decompose()

    skema = {}

    for dayNumber,day in enumerate(skemaDays):
        skema[titles[dayNumber]] = {}
        skema[titles[dayNumber]]["informationer"] = informations[dayNumber]

        skema[titles[dayNumber]]["skemaBrikker"] = []

        for skemaPiece in day.select("a.s2bgbox"):
            currentPiece = {"status" : "Uændret", "Title" : "", "Hold" : "", "Lærer" : "", "Lokale" : ""}
            currentPiece["link"] = f"https://lectio.dk{skemaPiece.get('href')}"
            pieceInformations = skemaPiece.get("data-additionalinfo").split("\n")

            for i in range(0, 2):
                if not datePattern.match(pieceInformations[i]) and pieceInformations[i] not in ["Aflyst!", "Ændret!"] and not pieceInformations[i].lower().startswith(("hold", "lærer", "lokale")):
                    currentPiece["Title"] = pieceInformations.pop(i)
                    break

            for pieceInformation in pieceInformations:
                dates = datePattern.findall(pieceInformation)
                times = timePattern.findall(pieceInformation)

                if dates != [] and times != []:
                    currentPiece["start"] = f"{dates[0]} {times[0]}"
                    currentPiece["slut"] = f"{dates[-1]} {times[-1]}"

                elif pieceInformation in ["Aflyst!", "Ændret!"]:
                    currentPiece["status"] = pieceInformation
                else:
                    for informationType in ["Hold", "Lærer", "Lokale"]:
                        if pieceInformation.lower().startswith(informationType.lower()):
                            currentPiece[informationType] = pieceInformation.split(": ")[-1]

            skema[titles[dayNumber]]["skemaBrikker"].append(currentPiece)

    return skema

def createTitleDict(titles, initialDict):
    if len(titles) < 2:
        return

    currentTitles = titles[0]

    for title in currentTitles:
        initialDict[title] = {}
        createTitleDict(titles[1:], initialDict[title])

def extractTable(tableSoup, titleHeight):

    tableSoup.select_one("tr:first-child th:first-child").decompose()

    titles = []

    collumns = tableSoup.find_all("tr")

    for i in range(titleHeight):
        titles.append([element.text for element in collumns[i].select("th")])

    titlesDict = {}

    createTitleDict(titles, titlesDict)

    dataDict = {}

    for row in itertools.islice(collumns, titleHeight, len(collumns)):

        currentRow = row.find_all("td")
        currentFag = currentRow.pop(0).text
        dataDict[currentFag] = copy.deepcopy(titlesDict)

        for i,collumn in enumerate(currentRow):
            currentTitles = [ titles[titleIndex][int((i / len(titles[-1])) * len(titles[titleIndex]))] for titleIndex in range(titleHeight) ]

            currentDataDict = dataDict[currentFag]

            for titleNumber in range(titleHeight - 1):
                currentDataDict = currentDataDict[currentTitles[titleNumber]]

            currentDataDict[currentTitles[-1]] = collumn.text.strip()

    return dataDict

def extractFravær(pageSoup):
    tableSoup = pageSoup.select_one("table#s_m_Content_Content_SFTabStudentAbsenceDataTable tbody:first-child")
    tableSoup.select_one("tr:first-child").decompose()
    return extractTable(tableSoup, 3)

def extractFraværImageURL(pageSoup):
    return "https://lectio.dk" + pageSoup.select_one("div#s_m_Content_Content_SFTabGraphicViewIsland_pa img:first-child").get("src")

def extractKarakterBevis(pageSoup):
    tableSoup = pageSoup.select_one("div#printareaDiplomaLines table tbody:first-child")
    return extractTable(tableSoup, 2)

def extractCurrentKarakterer(pageSoup):
    tableSoup = pageSoup.select_one("table#s_m_Content_Content_karakterView_KarakterGV tbody:first-child")

    for row in tableSoup.find_all("tr"):
        row.select_one("th:first-child,td:first-child").decompose()

    return extractTable(tableSoup, 1)

def extractKarakterComment(pageSoup):
    tableSoup = pageSoup.select_one("table#s_m_Content_Content_karakterView_KarakterNoterGrid tbody")
    return extractTable(tableSoup, 1)

def extractKarakterComment(pageSoup):
    tableSoup = pageSoup.select_one("table#s_m_Content_Content_karakterView_KarakterNoterGrid tbody")
    return extractTable(tableSoup, 1)

def extractKarakterProtokol(pageSoup):
    tableSoup = pageSoup.select_one("table#s_m_Content_Content_ProtokolLinierGrid tbody")

    for row in tableSoup.find_all("tr"):
        row.insert(0, row.find_all("td,th")[3])

    return extractTable(tableSoup, 1)
