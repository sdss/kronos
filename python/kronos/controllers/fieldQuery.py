# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint

from sdssdb.peewee.sdss5db import targetdb

from kronos.dbConvenience import getCadences, fieldQuery
from . import getTemplateDictBase

fieldQuery_page = Blueprint("fieldQuery_page", __name__)


def sortFunc(elem):
    return elem.field_id

@fieldQuery_page.route('/fieldQuery.html', methods=['GET', 'POST'])
async def fieldDetail():

    cadences = getCadences()

    templateDict = getTemplateDictBase()

    form = await request.form

    if "prioritizeField" in form:
        fieldPk = form["prioritizeField"]
        q = targetdb.Field.update(priority=2).where(targetdb.Field.pk == fieldPk)
        q.execute()
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    elif "disableField" in form:
        fieldPk = form["disableField"]
        q = targetdb.Field.update(priority=1).where(targetdb.Field.pk == fieldPk)
        q.execute()
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    elif "resetField" in form:
        fieldPk = form["resetField"]
        q = targetdb.Field.update(priority=0).where(targetdb.Field.pk == fieldPk)
        q.execute()
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

    if chosenCadence == "none":
        queryCadence = None
    else:
        queryCadence = chosenCadence

    if specialStatus == "none":
        dbPriority = None
    else:
        dbPriority = specialStatus
    fields = fieldQuery(cadence=queryCadence, priority=dbPriority)
    fields.sort(key=sortFunc)

    templateDict.update({
        "cadences": [str(c.label) for c in cadences],
        "specialStatus": specialStatus,
        "chosenCadence": chosenCadence,
        "fields": fields
    })

    return await render_template("fieldQuery.html", **templateDict)


if __name__ == "__main__":
    pass
