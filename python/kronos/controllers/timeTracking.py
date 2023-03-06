# -*- coding: utf-8 -*-
import shutil

from quart import request, render_template, Blueprint
import numpy as np

from kronos import wrapBlocking, observatory
from kronos.scheduler import offsetNow
from kronos.controllers.planObserving import nightBounds

from . import getTemplateDictBase

timeTracking_page = Blueprint("timeTracking_page", __name__)

@timeTracking_page.route('/timeTracking/', defaults={'mjd': None})
@timeTracking_page.route('/timeTracking/<int:mjd>', methods=['GET', 'POST'])
async def timeTracking(mjd):
    # mjd = round(offsetNow())

    templateDict = getTemplateDictBase()

    if "mjd" in request.args:
        mjd = int(request.args["mjd"])

    if mjd is None:
        mjd = round(offsetNow())
        templateDict.update({"mjd": mjd})
        return await render_template("timeTrackingLanding.html", **templateDict)

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

    if "Dqu" in request.args:
        update = True
        Btot = float(request.args["Btot"])
        Dtot = float(request.args["Dtot"])
        Dqu = float(request.args["Dqu"])
        Dcom = float(request.args["Dcom"])
        DLw = float(request.args["DLw"])
        DLtec = float(request.args["DLtec"])
        Bqu = float(request.args["Bqu"])
        Bcom = float(request.args["Bcom"])
        BLw = float(request.args["BLw"])
        BLtec = float(request.args["BLtec"])

    logName = "/data/logs/timetracking/timetracking.txt"
    logFile = await wrapBlocking(np.genfromtxt, logName, dtype=None,
                                 delimiter=",", names=True, encoding="UTF8")

    wTonight = np.where(logFile["MJD"] == mjd)
    if len(wTonight[0]):
        wTonight = int(wTonight[0])
    else:
        wTonight = None

    if update:
        if wTonight is None:
            nextIdx = int(logFile.shape[0]) + 1
            logFile.resize(nextIdx, refcheck=False)
            wTonight = nextIdx - 1
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

        header = "MJD , Observatory , Btot , Bqu , Bcom , BLw , BLtec , Dtot , Dqu , Dcom , DLw , DLtec"
        fmt = "%5d,%4s, %2.1f, %2.1f, %2.1f, %2.1f, %2.1f, %2.1f, %2.1f, %2.1f, %2.1f, %2.1f"

        await wrapBlocking(np.savetxt, logName, logFile,
                           delimiter=",", header=header, fmt=fmt, comments="")

    if not update:
        startTime, endTime, mjd_evening_twilight, mjd_morning_twilight,\
            evening_twilight_utc, morning_twilight_utc, brightDark, errors =\
            await nightBounds(mjd=mjd)

        if brightDark["Bright Start"]:
            Btot = (brightDark["Bright End"] - brightDark["Bright Start"]).seconds/3600
            Bqu = Btot
        if brightDark["Dark Start"]:
            Dtot = (brightDark["Dark End"] - brightDark["Dark Start"]).seconds/3600
            Dqu = Dtot

    doneAlready = False

    if wTonight:
        tonight = logFile[wTonight]
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

    templateDict.update({
        "Dtot": f"{Dtot:.1f}",
        "Btot": f"{Btot:.1f}",
        "Dqu": f"{Dqu:.1f}",
        "Dcom": f"{Dcom:.1f}",
        "DLw": f"{DLw:.1f}",
        "DLtec": f"{DLtec:.1f}",
        "Bqu": f"{Bqu:.1f}",
        "Bcom": f"{Bcom:.1f}",
        "BLw": f"{BLw:.1f}",
        "BLtec": f"{BLtec:.1f}",
        "update": update,
        "doneAlready": doneAlready,
        "mjd": mjd
    })

    return await render_template("timeTracking.html", **templateDict)
