from backend import extract
from backend.scraping import getPageSoup, getLoggedInPageSoup

import io

class Elev():
    def __init__(self, session, gymnasiumNumber, elevID = None):
        self.session = session
        self.gymnasiumNumber = gymnasiumNumber
        self.rootURL = f"https://www.lectio.dk/lectio/{gymnasiumNumber}/"

        if elevID:
            self.elevID = elevID
        else:
            frontPageSoup = getLoggedInPageSoup(self.rootURL, self.session)
            if frontPageSoup:
                self.elevID = extract.getElevID(frontPageSoup)
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

    def getImage(self, imageURL):
        print(imageURL)
        try:
            return io.BytesIO(self.session.get(imageURL).content)
        except TypeError:
            return None

    def getOpgaver(self, year):
        otherASPData = {"s$m$ChooseTerm$term" : str(year), "s$m$Content$Content$ShowThisTermOnlyCB" : "on"}
        opgaverSoup = self.postLoggedInPageSoup(f"{self.rootURL}OpgaverElev.aspx?elevid={self.elevID}", "s$m$ChooseTerm$term", otherASPData)
        return extract.extractOpgaver(opgaverSoup) if opgaverSoup else opgaverSoup

    def getLektier(self):
        lektierSoup = getLoggedInPageSoup(f"{self.rootURL}material_lektieoversigt.aspx?elevid={self.elevID}", self.session)
        return extract.extractLektier(lektierSoup) if lektierSoup else lektierSoup

    def getBeskeder(self, year, folderID):
        otherASPData = {"__EVENTARGUMENT" : str(folderID), "s$m$ChooseTerm$term" : str(year), "s$m$Content$Content$ListGridSelectionTree$folders" : str(folderID)}
        beskederSoup = self.postLoggedInPageSoup(f"{self.rootURL}beskeder2.aspx?elevid={self.elevID}", "s$m$Content$Content$ListGridSelectionTree", otherASPData)

        showAllEventTarget = extract.extractBeskederShowAllEventTarget(beskederSoup)
        if showAllEventTarget:
            otherASPData["__EVENTARGUMENT"] = ""
            beskederSoup = self.postLoggedInPageSoup(f"{self.rootURL}beskeder2.aspx?elevid={self.elevID}", showAllEventTarget, otherASPData)

        return extract.extractBeskeder(beskederSoup) if beskederSoup else beskederSoup

    def getBeskedContent(self, beskedID):
        beskedSoup = self.postLoggedInPageSoup(f"{self.rootURL}beskeder2.aspx?elevid={self.elevID}", "__Page", {"__EVENTARGUMENT" : beskedID})

        return extract.extractBesked(beskedSoup) if beskedSoup else beskedSoup

    def getSkema(self, year, week):
        skemaSoup = getLoggedInPageSoup(f"{self.rootURL}SkemaNy.aspx?type=elev&elevid={self.elevID}&week={str(week)}{str(year)}", self.session)

        return extract.extractSkema(skemaSoup) if skemaSoup else skemaSoup

    def getFravær(self, year, image=False):
        otherASPData = {"s$m$ChooseTerm$term" : str(year)}
        opgaverSoup = self.postLoggedInPageSoup(f"{self.rootURL}subnav/fravaerelev.aspx?elevid={self.elevID}", "s$m$ChooseTerm$term", otherASPData)
        if image and opgaverSoup:
            return self.getImage(extract.extractFraværImageURL(opgaverSoup))
        elif opgaverSoup:
            return extract.extractFravær(opgaverSoup)
        else:
            return opgaverSoup

    def getKarakterer(self, year, karakterType):
        otherASPData = {"s$m$ChooseTerm$term" : str(year)}
        karakterSoup = self.postLoggedInPageSoup(f"{self.rootURL}grades/grade_report.aspx?elevid={self.elevID}", "s$m$ChooseTerm$term", otherASPData)

        if not karakterSoup:
            return karakterSoup
        elif karakterType == "bevis":
            return extract.extractKarakterBevis(karakterSoup)
        elif karakterType == "nuværende":
            return extract.extractCurrentKarakterer(karakterSoup)
        elif karakterType == "kommentar":
            return extract.extractKarakterComment(karakterSoup)
        elif karakterType == "protokol":
            return extract.extractKarakterProtokol(karakterSoup)
        else:
            return False
