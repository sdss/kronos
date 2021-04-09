# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint

from kronos.dbConvenience import getCadences, fieldQuery
from . import getTemplateDictBase

fieldQuery_page = Blueprint("fieldQuery_page", __name__)


@fieldQuery_page.route('/fieldQuery.html', methods=['GET', 'POST'])
async def fieldDetail():

    cadences = getCadences()

    templateDict = getTemplateDictBase()

    if request.args:
        chosenCadence = request.args["cadence"]

        specialStatus = request.args["specialStatus"]
    else:
        specialStatus = "none"
        chosenCadence = "Cadence"

    if chosenCadence == "Cadence":
        queryCadence = None
    else:
        queryCadence = chosenCadence

    fields = fieldQuery(cadence=queryCadence)

    templateDict.update({
        "cadences": [str(c.label) for c in cadences],
        "specialStatus": specialStatus,
        "chosenCadence": chosenCadence,
        "fields": fields
    })

    return await render_template("fieldQuery.html", **templateDict)


if __name__ == "__main__":
    pass
