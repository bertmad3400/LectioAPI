from backend.extract import getElevID
from backend.scraping import getPageSoup, getLoggedInPageSoup


class Elev():
    def __init__(self, session, gymnasiumNumber):
        self.session = session
        self.rootURL = f"https://www.lectio.dk/lectio/{gymnasiumNumber}/"
        self.elevID = getElevID(session.get(rootURL).content)
