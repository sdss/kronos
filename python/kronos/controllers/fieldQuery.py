# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint

from sdssdb.peewee.sdss5db import targetdb, opsdb

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
