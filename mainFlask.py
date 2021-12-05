from flask import Flask, render_template, Response, request, abort, redirect, make_response, g
import json

import uuid

from Crypto.Hash import SHA256

from backend.login import loginUser
from backend.objects import Elev

app = Flask(__name__)
app.static_folder = "./static"
app.template_folder = "./templates"

elevDicts = {}

def createInternalID(username, password):
    return SHA256.new(f"{username}%%%{password}".encode("utf-8")).hexdigest()

def removeElev(username, password):
    internalID = createInternalID(username, password)

    for elevID in list(elevDicts.keys()):
        if elevDicts[elevID]["internalID"] == internalID:
            del elevDicts[elevID]

def addElev(username, password, elevObject):

    internalID = createInternalID(username, password)

    removeElev(username, password)

    currentElevID = str(uuid.uuid4())

    elevDicts[currentElevID] = {"elevObject" : elevObject, "internalID" : internalID}

    return currentElevID

@app.before_request
def extractUserObject():
    elevID = request.cookies.get("LectioAPI-ID", default=None)

    if not request.endpoint in ["login", "redirectToGithub"] and elevID:
        g.currentElev = elevDicts[elevID]["elevObject"]
    elif not request.endpoint in ["login", "redirectToGithub"]:
        abort(401)

def returnAPIResult(APIResults):
    if APIResults == None:
        abort(401)
    else:
        return Response(json.dumps(APIResults), mimetype="application/json")

@app.route("/")
def redirectToGithub():
    return redirect("https://github.com/bertmad3400/LectioAPI")

@app.route("/login", methods=["POST"])
def login():
    parameters = request.get_json(force=True)

    userSession = loginUser(parameters["username"], parameters["password"], parameters["gymnasiumNumber"])

    if userSession:
        try:
            currentElev = Elev(userSession, 3)
        except TypeError:
            abort(500)

        currentElevID = addElev(parameters["username"], parameters["password"],currentElev)

        resp = make_response("user succesfully logged in")

        resp.set_cookie("LectioAPI-ID", value = currentElevID, secure = True, httponly = True)

        return resp

    else:
        abort(500)

@app.route("/beskedListe/<string:beskedClass>/<int:year>/")
def queryBeskeder(beskedClass, year):
    beskedClasses = {
            "nyeste" : "-70",
            "ulæste" : "-40",
            "flag" : "-50",
            "slettede" : "-60",
            "egne" : "-10",
            "sendte" : "-80",
            "hold" : "-20",
            "indbyggedegrupper" : "-30",
            "egnegrupper" : "-35"
            }

    if beskedClass in beskedClasses:
        APIResponse = g.currentElev.getBeskeder(year, beskedClasses[beskedClass])
        return returnAPIResult(APIResponse)
    else:
        return make_response("Besked class not found", 404)

@app.route("/beskedIndhold/<string:beskedID>/")
def queryBeskedContent(beskedID):
    APIResponse = g.currentElev.getBeskedContent(beskedID)
    return returnAPIResult(APIResponse)

@app.route("/opgaveListe/<int:year>/")
def queryOpgaver(year):
    APIResponse = g.currentElev.getOpgaver(year)
    return returnAPIResult(APIResponse)

@app.route("/lektieList/")
def queryLektier():
    APIResponse = g.currentElev.getLektier()
    return returnAPIResult(APIResponse)


if __name__ == "__main__":
    app.run(debug=True)
