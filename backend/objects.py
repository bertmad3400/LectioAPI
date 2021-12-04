from backend.extract import getElevID, extractASPData
from backend.scraping import getPageSoup, getLoggedInPageSoup


class Elev():
    def __init__(self, session, gymnasiumNumber):
        self.session = session
        self.rootURL = f"https://www.lectio.dk/lectio/{gymnasiumNumber}/"

        self.frontPageSoup = getLoggedInPageSoup(self.rootURL, self.session)

        if self.frontPageSoup:
            self.elevID = getElevID(self.frontPageSoup)
        else:
            return False

    def postLoggedInPageSoup(self, URL, eventTarget, otherASPData):
        getResponse = getLoggedInPageSoup(URL, self.session)

        if getResponse:
            ASPData = extractASPData(getResponse, eventTarget)
            ASPData.update(otherASPData)

            return getLoggedInPageSoup(URL, self.session, ASPData)

        else:
            return None
