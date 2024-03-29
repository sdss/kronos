# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint
import numpy as np

from kronos import wrapBlocking
from kronos.scheduler import Scheduler
from kronos.dbConvenience import designQuery, cartonLabels
from kronos.controllers.fieldQuery import getRaRange
from kronos.controllers.planObserving import nightBounds
from . import getTemplateDictBase

designQuery_page = Blueprint("designQuery_page", __name__)


def sortFunc(elem):
    return elem.field_id


@designQuery_page.route('/designQuery.html', methods=['GET', 'POST'])
async def designDetail():

    ra_start, ra_end = await getRaRange()

    templateDict = getTemplateDictBase()

    fieldid = "none"
    completionStatus = "all"
    instrument = "BOSS"
    chosenCarton = "none"
    orderby = "RA"
    design_ids = list()
    errors = list()

    pa_start = 0
    pa_end = 360
    includeCustom = True
    limit = 100

    if request.args:
        if "designs" in request.args:
            d_text = request.args["designs"]
            if len(d_text) > 0:
                try:
                    if "," in d_text:
                        design_ids = [int(d) for d in d_text.strip().split(",") if len(d)]
                    else:
                        design_ids = [int(d_text)]
                except:
                    errors.append("invalid design input")
                    design_ids = list()
        fieldid = request.args["fieldid"].strip()
        if len(fieldid) == 0:
            fieldid = "none"
        completionStatus = request.args["completionStatus"]
        instrument = request.args["instrument"]
        orderby = request.args["orderby"]
        try:
            ra_start = int(request.args["ra0Select"])
            ra_end = int(request.args["ra1Select"])
        except:
            ra_start = 0
            ra_end = 360
        try:
            pa_start = float(request.args["pa0Select"])
            pa_end = float(request.args["pa1Select"])
        except:
            pa_start = 0
            pa_end = 360
        chosenCarton = request.args["carton"].strip()
        includeCustom = "includeCustom" in request.args
    else:
        limit = 10

    cartons = await wrapBlocking(cartonLabels)

    if fieldid == "none":
        queryid = None
    else:
        queryid = fieldid

    ra_range = [int(ra_start), int(ra_end)]
    pa_range = [float(pa_start), float(pa_end)]

    if completionStatus == "notStarted":
        dbStatus = "not started"
    elif completionStatus == "inProgress":
        dbStatus = "started"
    elif completionStatus == "done":
        dbStatus = "done"
    else:
        dbStatus = None

    # empty string keeps being sent by form, deal with it later
    if chosenCarton == "none" or len(chosenCarton) == 0:
        queryCarton = None
    else:
        queryCarton = chosenCarton

    designs = await wrapBlocking(designQuery,
                                 field_id=queryid,
                                 ra_range=ra_range,
                                 dbStatus=dbStatus,
                                 carton=queryCarton,
                                 pa_range=pa_range,
                                 orderby=orderby,
                                 instrument=instrument,
                                 design_ids=design_ids,
                                 includeCustom=includeCustom,
                                 limit=limit)
    if instrument == "BOSS":
        oinstrument = "APOGEE"
    else:
        oinstrument = "BOSS"

    sched = await wrapBlocking(Scheduler)
    rs = sched.scheduler
    startTime, endTime, mjd_evening_twilight, mjd_morning_twilight,\
        evening_twilight_utc, morning_twilight_utc, brightDark, errors =\
    await nightBounds(scheduler=sched)

    ra = np.array([d["racen"] for d in designs])
    dec = np.array([d["deccen"] for d in designs])
    
    mjds = np.linspace(mjd_evening_twilight, mjd_morning_twilight, 9)

    for d in designs:
        d["airmass"] = list()
    for m in mjds:
        alt, az = rs.radec2altaz(mjd=m, ra=ra, dec=dec)
        am = rs.alt2airmass(alt)
        for i, a in enumerate(am):
            if a > 4 or a < 1:
                designs[i]["airmass"].append(9)
            else:
                designs[i]["airmass"].append(a)

    templateDict.update({
        "errorMsg": errors,
        "fieldid": fieldid,
        "completionStatus": completionStatus,
        "ra_range": ra_range,
        "pa_range": pa_range,
        "designs": designs,
        "cartons": cartons,
        "carton": chosenCarton,
        "instrument": instrument,
        "oinstrument": oinstrument,
        "orderby": orderby,
        "design_ids": design_ids,
        "includeCustom": includeCustom
    })

    return await render_template("designQuery.html", **templateDict)


if __name__ == "__main__":
    pass
