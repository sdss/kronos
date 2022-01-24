# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint
from astropy.time import Time

from sdssdb.peewee.sdss5db import targetdb, opsdb

from kronos import wrapBlocking
from kronos.scheduler import Scheduler
from kronos.dbConvenience import designQuery, cartonLabels
from kronos.controllers.fieldQuery import getRaRange
from . import getTemplateDictBase

designQuery_page = Blueprint("designQuery_page", __name__)


def sortFunc(elem):
    return elem.field_id


@designQuery_page.route('/designQuery.html', methods=['GET', 'POST'])
async def designDetail():

    ra_start, ra_end = await getRaRange()

    templateDict = getTemplateDictBase()

    form = await request.form

    fieldid = "none"
    completionStatus = "all"
    instrument = "BOSS"
    chosenCarton = "none"
    orderby = "RA"

    pa_start = 0
    pa_end = 360

    if request.args:
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
                                 orderby=orderby)

    templateDict.update({
        "fieldid": fieldid,
        "completionStatus": completionStatus,
        "ra_range": ra_range,
        "pa_range": pa_range,
        "designs": designs,
        "cartons": cartons,
        "carton": chosenCarton,
        "instrument": instrument,
        "orderby": orderby
    })

    return await render_template("designQuery.html", **templateDict)


if __name__ == "__main__":
    pass
