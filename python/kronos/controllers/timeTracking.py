# -*- coding: utf-8 -*-
import shutil

from quart import request, render_template, Blueprint
import numpy as np

from kronos import wrapBlocking, observatory
from kronos.scheduler import offsetNow

timeTracking_page = Blueprint("timeTracking_page", __name__)


@timeTracking_page.route('/timeTracking.html', methods=['GET', 'POST'])
async def timeTracking():
    mjd = round(offsetNow())

    Btot = 0.0
    Dtot = 0.0
    Dqu = 0.0
    Dcom = 0.0
    DLw = 0.0
    DLtec = 0.0
    Bqu = 0.0
    Bcom = 0.0
    BLw = 0.0
    BLtec = 0.0

    update = False

    form = await request.form
    if "Dqu" in form:
        update = True
        Btot = form["Btot"]
        Dtot = form["Dtot"]
        Dqu = form["Dqu"]
        Dcom = form["Dcom"]
        DLw = form["DLw"]
        DLtec = form["DLtec"]
        Bqu = form["Bqu"]
        Bcom = form["Bcom"]
        BLw = form["BLw"]
        BLtec = form["BLtec"]

    logName = "/data/logs/timetracking/timetracking.txt"
    logFile = wrapBlocking(np.genfromtxt, logName, dtype=None, delimiter=",",
                           names=True, encoding="UTF8")

    wTonight = np.where(logFile["MJD"] == mjd)

    if not len(wTonight[0]):
        nextIdx = logFile.shape[0] + 1
        logFile.resize(nextIdx)
        wTonight = nextIdx - 1

    if update:
        shutil.copyfile(logName, f"/data/logs/timetracking/timetracking_{mjd}.dat")

        logFile[wTonight]["Dtot"] = Dtot
        logFile[wTonight]["Dqu"] = Dqu
        logFile[wTonight]["Dcom"] = Dcom
        logFile[wTonight]["DLw"] = DLw
        logFile[wTonight]["DLtec"] = DLtec

        logFile[wTonight]["Btot"] = Btot
        logFile[wTonight]["Bqu"] = Bqu
        logFile[wTonight]["Bcom"] = Bcom
        logFile[wTonight]["BLw"] = BLw
        logFile[wTonight]["BLtec"] = BLtec

        logFile[wTonight]["MJD"] = mjd
        logFile[wTonight]["Observatory"] = observatory.upper()

        await wrapBlocking(np.savetxt, logName, logFile, delimiter=",")

    if not update:
        startTime, endTime, mjd_evening_twilight, mjd_morning_twilight,\
            evening_twilight_utc, morning_twilight_utc, brightDark, errors =\
            await nightBounds(mjd=mjd)

        if brightDark["Bright Start"]:
            Btot = (brightDark["Bright End"] - brightDark["Bright Start"]).hours
        if brightDark["Dark Start"]:
            Dtot = (brightDark["Dark End"] - brightDark["Dark Start"]).hours

    doneAlready = False

    tonight = logFile[wTonight]

    if len(tonight) == 1:
        doneAlready = True
        Dtot = tonight["Dtot"]
        Dqu = tonight["Dqu"]
        Dcom = tonight["Dcom"]
        DLw = tonight["DLw"]
        DLtec = tonight["DLtec"]

        Btot = tonight["Btot"]
        Bqu = tonight["Bqu"]
        Bcom = tonight["Bcom"]
        BLw = tonight["BLw"]
        BLtec = tonight["BLtec"]

    templateDict = getTemplateDictBase()

    templateDict.update({
        "Dtot": Dtot,
        "Btot": Btot,
        "Dqu": Dqu,
        "Dcom": Dcom,
        "DLw": DLw,
        "DLtec": DLtec,
        "Bqu": Bqu,
        "Bcom": Bcom,
        "BLw": BLw,
        "BLtec": BLtec,
        "update": update,
        "doneAlready": doneAlready,
        "mjd": mjd,
        "errorMsg": errors
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("timeTracking.html", **templateDict)
