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
    if "login.aspx?prevurl" in pageResponse.url:
        return None
    else:
        pageSoup = bs(pageResponse.content, "html5lib")
        if "Der opstod en ukendt fejl" in pageSoup.text:
            return False
        else:
            return pageSoup
