from flask import Flask, render_template, Response, request, abort, redirect, make_response
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

if __name__ == "__main__":
    app.run(debug=True)
