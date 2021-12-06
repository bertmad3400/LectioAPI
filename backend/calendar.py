def opgaverToCalendar(opgaveDicts):
    opgaveLists = [["Subject", "Description", "Start Date", "All Day Event"]]
    for opgaveDict in opgaveDicts:
        if opgaveDict["Status"] == "Venter" and opgaveDict["Afventer"] == "Elev":
            date = opgaveDict["Frist"].replace("-", "/").split(" ")
            opgaveLists.append([opgaveDict["Opgavetitel"], opgaveDict["Hold"], date[0], "True"]) 

    return opgaveLists
