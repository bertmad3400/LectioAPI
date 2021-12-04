from backend import extract
from backend.scraping import getPageSoup, getLoggedInPageSoup


class Elev():
    def __init__(self, session, gymnasiumNumber):
        self.session = session
        self.rootURL = f"https://www.lectio.dk/lectio/{gymnasiumNumber}/"

        self.frontPageSoup = getLoggedInPageSoup(self.rootURL, self.session)

        if self.frontPageSoup:
            self.elevID = extract.getElevID(self.frontPageSoup)
        else:
            return False

    def postLoggedInPageSoup(self, URL, eventTarget, otherASPData):
        getResponse = getLoggedInPageSoup(URL, self.session)

        if getResponse:
            ASPData = extract.extractASPData(getResponse, eventTarget)
            ASPData.update(otherASPData)

            return getLoggedInPageSoup(URL, self.session, ASPData)

        else:
            return None

    def getOpgaver(self, year):
        otherASPData = {"s$m$ChooseTerm$term" : str(year), "s$m$Content$Content$ShowThisTermOnlyCB" : "on"}
        opgaverSoup = self.postLoggedInPageSoup(f"{self.rootURL}OpgaverElev.aspx?elevid={self.elevID}", "s$m$ChooseTerm$term", otherASPData)
        return extract.extractOpgaver(opgaverSoup)

    def getLektier(self):
        lektierSoup = getLoggedInPageSoup(f"{self.rootURL}material_lektieoversigt.aspx?elevid={self.elevID}", self.session)
        return extract.extractLektier(lektierSoup)

    def getBeskeder(self, year, folderID):
        otherASPData = {"__EVENTARGUMENT" : str(folderID), "s$m$ChooseTerm$term" : str(year), "s$m$Content$Content$ListGridSelectionTree$folders" : str(folderID)}
        beskederSoup = self.postLoggedInPageSoup(f"{self.rootURL}beskeder2.aspx?elevid={self.elevID}", "s$m$Content$Content$ListGridSelectionTree", otherASPData)

        showAllEventTarget = extract.extractBeskederShowAllEventTarget(beskederSoup)
        if showAllEventTarget:
            otherASPData["__EVENTARGUMENT"] = ""
            beskederSoup = self.postLoggedInPageSoup(f"{self.rootURL}beskeder2.aspx?elevid={self.elevID}", showAllEventTarget, otherASPData)

        return extract.extractBeskeder(beskederSoup)

    def getBeskedContent(self, beskedID):
        beskedSoup = self.postLoggedInPageSoup(f"{self.rootURL}beskeder2.aspx?elevid={self.elevID}", "__Page", {"__EVENTARGUMENT" : beskedID})

        return extract.extractBesked(beskedSoup)
