# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint
from astropy.time import Time

from sdssdb.peewee.sdss5db import targetdb, opsdb

from kronos.scheduler import Scheduler
from kronos.dbConvenience import getCadences, fieldQuery
from . import getTemplateDictBase

fieldQuery_page = Blueprint("fieldQuery_page", __name__)


def sortFunc(elem):
    return elem.field_id

@fieldQuery_page.route('/fieldQuery.html', methods=['GET', 'POST'])
async def fieldDetail():

    now = Time.now()
    now.format = "mjd"
    mjd_now = now.value
    # use an offset so "tonight" is used until 15:00 UTC
    offset = 3 / 24
    mjd = round(mjd_now - offset)

    scheduler = Scheduler(observatory="apo")

    mjd_evening_twilight, mjd_morning_twilight = scheduler.getNightBounds(mjd)
    ra_start = float(scheduler.scheduler.lst(mjd_evening_twilight) - 45 + 360) % 360
    ra_end = float(scheduler.scheduler.lst(mjd_morning_twilight) + 45) % 360

    cadences = getCadences()

    templateDict = getTemplateDictBase()

    form = await request.form

    if "prioritizeField" in form:
        fieldPk = form["prioritizeField"]
        dbPriority = opsdb.FieldPriority.get(label="top")
        f2p, created = opsdb.FieldToPriority.get_or_create(field_pk=fieldPk)
        f2p.FieldPriority = dbPriority
        f2p.save()
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    elif "disableField" in form:
        fieldPk = form["disableField"]
        dbPriority = opsdb.FieldPriority.get(label="disabled")
        f2p, created = opsdb.FieldToPriority.get_or_create(field_pk=fieldPk)
        f2p.FieldPriority = dbPriority
        f2p.save()
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    elif "resetField" in form:
        fieldPk = form["resetField"]
        q = opsdb.FieldToPriority.delete().where(opsdb.FieldToPriority.field_pk == fieldPk)
        removed = q.execute()
        assert removed != 0, "Should not have been able to delete"
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
    fields = fieldQuery(cadence=queryCadence, priority=dbPriority, ra_range=[ra_start, ra_end])
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
