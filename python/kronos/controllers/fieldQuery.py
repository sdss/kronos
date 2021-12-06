# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint

from sdssdb.peewee.sdss5db import targetdb, opsdb

from kronos import wrapBlocking
from kronos.scheduler import Scheduler, offsetNow
from kronos.dbConvenience import getCadences, fieldQuery, prioritizeField, disableField, resetField
from . import getTemplateDictBase

fieldQuery_page = Blueprint("fieldQuery_page", __name__)


async def getRaRange():
    mjd = round(offsetNow())

    scheduler = Scheduler()

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, mjd)
    ra_start = await wrapBlocking(scheduler.scheduler.lst, mjd_evening_twilight)
    ra_start = float(ra_start - 45 + 360) % 360
    ra_end = await wrapBlocking(scheduler.scheduler.lst, mjd_morning_twilight)
    ra_end = float(ra_end + 45) % 360

    return ra_start, ra_end


def sortFunc(elem):
    return elem.field_id


@fieldQuery_page.route('/fieldQuery.html', methods=['GET', 'POST'])
async def fieldDetail():

    ra_start, ra_end = await getRaRange()

    cadences = getCadences()

    templateDict = getTemplateDictBase()

    form = await request.form

    if "prioritizeField" in form:
        fieldPk = form["prioritizeField"]
        await wrapBlocking(prioritizeField, fieldPk)
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    elif "disableField" in form:
        fieldPk = form["disableField"]
        await wrapBlocking(disableField, fieldPk)
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    elif "resetField" in form:
        fieldPk = form["resetField"]
        await wrapBlocking(resetField, fieldPk)
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    else:
        # set default, can change it below
        specialStatus = "none"
        chosenCadence = "none"

    if request.args:
        chosenCadence = request.args["cadence"].strip()
        if len(chosenCadence) == 0:
            chosenCadence = "none"
        specialStatus = request.args["specialStatus"]
        try:
            ra_start = int(request.args["ra0Select"])
            ra_end = int(request.args["ra1Select"])
        except:
            ra_start = 0
            ra_end = 360

    if chosenCadence == "none":
        queryCadence = None
    else:
        queryCadence = chosenCadence

    if specialStatus == "none":
        dbPriority = None
    else:
        dbPriority = specialStatus
    fields = await wrapBlocking(fieldQuery,
                                cadence=queryCadence,
                                priority=dbPriority,
                                ra_range=[ra_start, ra_end])
    fields.sort(key=sortFunc)

    templateDict.update({
        "cadences": [str(c.label) for c in cadences],
        "specialStatus": specialStatus,
        "chosenCadence": chosenCadence,
        "fields": fields,
        "ra_range": [int(ra_start), int(ra_end)]
    })

    return await render_template("fieldQuery.html", **templateDict)


if __name__ == "__main__":
    pass
