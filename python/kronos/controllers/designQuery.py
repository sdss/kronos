# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint
from astropy.time import Time

from sdssdb.peewee.sdss5db import targetdb, opsdb

from kronos import wrapBlocking
from kronos.scheduler import Scheduler
from kronos.dbConvenience import designQuery
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

    if request.args:
        fieldid = request.args["fieldid"].strip()
        if len(fieldid) == 0:
            fieldid = "none"
        completionStatus = request.args["completionStatus"]
        try:
            ra_start = int(request.args["ra0Select"])
            ra_end = int(request.args["ra1Select"])
        except:
            ra_start = 0
            ra_end = 360

    # fields = await wrapBlocking(fieldQuery,
    #                             cadence=queryCadence,
    #                             priority=dbPriority,
    #                             ra_range=[ra_start, ra_end])
    # fields.sort(key=sortFunc)

    if fieldid == "none":
        queryid = None
    else:
        queryid = fieldid

    ra_range = [int(ra_start), int(ra_end)]

    designs = await wrapBlocking(designQuery,
                                 field_id=queryid,
                                 ra_range=ra_range)

    templateDict.update({
        "fieldid": fieldid,
        "completionStatus": completionStatus,
        "ra_range": ra_range,
        "designs": designs
    })

    return await render_template("designQuery.html", **templateDict)


if __name__ == "__main__":
    pass
