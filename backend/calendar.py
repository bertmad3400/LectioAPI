from io import StringIO
import csv

def generateCSVObject(contentList):
    CSVObject = StringIO()
    w = csv.writer(CSVObject)

    for row in contentList:
        w.writerow(row)
        yield CSVObject.getvalue()
        CSVObject.seek(0)
        CSVObject.truncate(0)

def opgaverToCalendar(opgaveDicts):
    opgaveLists = [["Subject", "Description", "Start Date", "All Day Event"]]
    for opgaveDict in opgaveDicts:
        if opgaveDict["Status"] == "Venter" and opgaveDict["Afventer"] == "Elev":
            date = opgaveDict["Frist"].replace("-", "/").split(" ")
            opgaveLists.append([opgaveDict["Opgavetitel"], opgaveDict["Hold"], date[0], "True"]) 

    return opgaveLists
