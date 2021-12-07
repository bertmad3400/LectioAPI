from io import StringIO
import csv
from datetime import datetime

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

def kalenderToCalendar(skemaDicts):
    skemaList = [["Subject", "Start Date", "Start Time", "End Time", "Description"]]
    for week in skemaDicts:
        for day in skemaDicts[week]:
            for skemaBrik in skemaDicts[week][day]["skemaBrikker"]:
                if skemaBrik["status"] in ["Ændret!", "Uændret"]:
                    date = {}
                    time = {}
                    for dateDescription in ["start", "slut"]:
                        date[dateDescription] = skemaBrik[dateDescription].replace("-", "/").split(" ")[0]
                        time[dateDescription] = datetime.strptime(skemaBrik[dateDescription].split(" ")[1], "%H:%M").strftime("%I:%M %p")

                    skemaList.append([f"{skemaBrik['Hold']} {skemaBrik['Lokale']}", date["start"], time["start"], date["slut"], time["slut"], f"{skemaBrik['Title']} med {skemaBrik['Lærer']}" if skemaBrik["Title"] else skemaBrik["Lærer"]])
    return skemaList
