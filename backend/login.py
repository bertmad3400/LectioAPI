from backend.scraping import getPageSoup
from backend.extract import extractASPData

import requests


# Function for returning a logged in user
def loginUser(username, password, gymnasiumNumber):
    loginURL = f"https://www.lectio.dk/lectio/{gymnasiumNumber}/login.aspx"

    with requests.session() as session:
        session.headers['user-agent'] = 'Mozilla/5.0'

        loginPageSoup = getPageSoup(loginURL, session=session)

        ASPData = extractASPData(loginPageSoup, "m$Content$submitbtn2")

        ASPData["m$Content$username"] = username
        ASPData["m$Content$password"] = password

        session.post(loginURL, data=ASPData)

    return session
