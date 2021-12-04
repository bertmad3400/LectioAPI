import requests
from bs4 import BeautifulSoup as bs

def getPageSoup(URL, session=None):
    if session != None:
        getResponse = session.get(URL)
    else:
        getResponse = requests.get(URL)

    return bs(getResponse.content, "html5lib")


def getLoggedInPageSoup(URL, session, ASPData = None):

    if ASPData:
        pageResponse = session.post(URL, data=ASPData)
    else:
        pageResponse = session.get(URL)

    # To check if the URL has redirected to the loginpage, in which case the session is invalid
    if pageResponse.url.startswith("https://www.lectio.dk/lectio/3/login.aspx?prevurl"):
        return None
    else:
        return bs(pageResponse.content, "html5lib")
