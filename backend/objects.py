from backend.extract import getElevID
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
