from flask import Flask, render_template, Response, request, abort, redirect, make_response, g, stream_with_context, url_for
from werkzeug.datastructures import Headers
import json

import uuid

import sqlite3
import pickle
import os

from Crypto.Hash import SHA256

import secrets

from pathlib import Path

import forms
from backend.scraping import getPageSoup
from backend.extract import extractGymnasiumList
from backend.login import loginUser
from backend.objects import Elev
from backend.calendar import opgaverToCalendar, generateCSVObject

app = Flask(__name__)
app.static_folder = "./webfront/static"
app.template_folder = "./webfront/templates"

dbName = "users.db"

# Endpoints that are allowed without logging ind
allowedEndpoints = ["getCalendarFile", "listGymnasiums", "login", "redirectToGithub"]

def loadSecretKey():
    if os.path.isfile("./secret.key"):
        app.secret_key = Path("./secret.key").read_text()
    else:
        currentSecretKey = secrets.token_urlsafe(256)
        with os.fdopen(os.open(Path("./secret.key"), os.O_WRONLY | os.O_CREAT, 0o400), 'w') as file:
            file.write(currentSecretKey)
        app.secret_key = currentSecretKey

def initiateDB():
    if os.path.exists(dbName):
        os.remove(dbName)

    conn = sqlite3.connect(dbName)
    cur = conn.cursor()

    cur.execute("CREATE TABLE users (internalID text PRIMARY KEY, externalID text, elevid integer, gymnasiumnumber integer, sessionobject blob)")

    conn.commit()

    conn.close()

def createInternalID(username, password):
    return SHA256.new(f"{username}%%%{password}".encode("utf-8")).hexdigest()

def removeElev(conn, ID, internal):
    cur = conn.cursor()
    if internal:
        cur.execute("DELETE FROM users WHERE internalID=?", (ID,))
    else:
        cur.execute("DELETE FROM users WHERE externalID=?", (ID,))

    conn.commit()

def addElev(username, password, elevObject):

    conn = sqlite3.connect(dbName)

    internalID = createInternalID(username, password)
    externalID = str(uuid.uuid4())

    removeElev(conn, internalID, True)

    cur = conn.cursor()
    cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (internalID, externalID, elevObject.elevID, elevObject.gymnasiumNumber, pickle.dumps(elevObject.session)))

    conn.commit()
    conn.close()

    return externalID

def loadElev(externalID):

    conn = sqlite3.connect(dbName)
    cur = conn.cursor()

    cur.execute("SELECT elevid, gymnasiumnumber, sessionobject FROM users WHERE externalID=?", (externalID,))

    dbResults = cur.fetchone()

    currentElev = Elev(pickle.loads(dbResults[2]), dbResults[1], elevID = dbResults[0])

    conn.close()

    return currentElev

@app.before_request
def extractUserObject():

    externalID = request.cookies.get("LectioAPI-ID", default=None)

    if not request.endpoint in allowedEndpoints and externalID:
        g.currentElev = loadElev(externalID)
    elif not request.endpoint in allowedEndpoints and not request.path.startswith("/static/"):
        abort(401)

def returnAPIResult(APIResults):
    if APIResults == None:

        externalID = request.cookies.get("LectioAPI-ID", default=None)

        resp = make_response("Couldn't access the relevant page", 401)

        if externalID:
            conn = sqlite3.connect(dbName)
            removeElev(conn, externalID, False)
            conn.close()

            resp.set_cookie("LectioAPI-ID", "", expires=0, secure = True, httponly = True)

        return resp
    elif APIResults == False:
        return make_response("Error scraping the page, please check your request", 400)
    else:
        return Response(json.dumps(APIResults), mimetype="application/json")

def returnCSVFile(filename, contentList):
    fileHeaders = Headers()
    fileHeaders.add('Content-Disposition', f'attachment; filename={filename}.csv')

    return app.response_class(stream_with_context(generateCSVObject(contentList)), mimetype='text/csv', headers=fileHeaders)

@app.route("/")
def redirectToGithub():
    return redirect("https://github.com/bertmad3400/LectioAPI")

@app.route("/gymnasieListe/")
def listGymnasiums():
    return returnAPIResult(extractGymnasiumList(getPageSoup("https://www.lectio.dk/lectio/login_list.aspx?showall=1")))


@app.route("/login/", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        gymnasiumNumber = form.gymnasiumNumber.data

    elif request.method == "POST":

        parameters = request.get_json(force=True)

        username = parameters["username"]
        password = parameters["password"]
        gymnasiumNumber = parameters["gymnasiumNumber"]

    else:

        return render_template("login.html", form=form)

    userSession = loginUser(username, password, gymnasiumNumber)

    if userSession:
        try:
            currentElev = Elev(userSession, int(gymnasiumNumber))
        except TypeError:
            abort(500)

        currentElevID = addElev(username, password, currentElev)

        resp = redirect(url_for("index"))

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

@app.route("/lektieListe/")
def queryLektier():
    APIResponse = g.currentElev.getLektier()
    return returnAPIResult(APIResponse)

@app.route("/skema/<int:year>/<int:week>/")
def querySkema(year, week):
    APIResponse = g.currentElev.getSkema(year, week)
    return returnAPIResult(APIResponse)

@app.route("/kalendar/opgaver/<int:year>/")
def getCalendarFile(year):

    opgaver = g.currentElev.getOpgaver(year)
    calendarListe = opgaverToCalendar(opgaver)

    return returnCSVFile("opgaveKalendar", calendarListe)

loadSecretKey()

if __name__ == "__main__":
    initiateDB()
    app.run(debug=True)
