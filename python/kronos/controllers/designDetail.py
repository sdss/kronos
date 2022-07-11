# -*- coding: utf-8 -*-
import asyncio

from quart import request, render_template, Blueprint

import numpy as np
from peewee import DoesNotExist

from sdssdb.peewee.sdss5db import targetdb, opsdb

from kronos import wrapBlocking, rs_version
from kronos.dbConvenience import getConfigurations, designDetails, safeInsertInQueue, safeAppendQueue
from kronos.scheduler import offsetNow, Scheduler

from . import getTemplateDictBase

designDetail_page = Blueprint("designDetail_page", __name__)


@designDetail_page.route('/designDetail.html', methods=['GET', 'POST'])
async def designDetail():

    dbField = targetdb.Field
    dbDesign = targetdb.Design

    form = await request.form

    scheduler = await wrapBlocking(Scheduler)

    mjd = offsetNow()

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, round(mjd))

    if mjd < mjd_evening_twilight:
        mjd = mjd_evening_twilight

    if "insert_design_id" in form:
        insert_design = int(form["insert_design_id"])
        pos = int(form["position"])
        if pos == 0:
            pos = 1
        q_mjd = None
        if pos == 1:
            q_mjd = mjd
        await wrapBlocking(safeInsertInQueue, insert_design, pos, mjd_plan=q_mjd)
    elif "append_design_id" in form:
        append_design = int(form["append_design_id"])
        await wrapBlocking(safeAppendQueue, append_design, mjd_plan=mjd)

    designID = int(request.args["designID"])

    try:
        design = await wrapBlocking(dbDesign.get, designID)
    except DoesNotExist:
        return await render_template('404.html'), 404

    status, cartons, fiberCounts = await wrapBlocking(designDetails, design)

    d2f = targetdb.DesignToField

    d2f_query = d2f.select()\
                   .join(targetdb.Design,
                         on=(targetdb.Design.design_id == d2f.design_id))\
                   .switch(d2f)\
                   .join(targetdb.Field, on=(targetdb.Field.pk == d2f.field_pk))\
                   .join(targetdb.Version)\
                   .where(targetdb.Design.design_id == designID,
                          targetdb.Version.plan == rs_version)
    this_d2f = await wrapBlocking(d2f_query.first)

    field = await wrapBlocking(dbField.get, pk=this_d2f.field_pk)

    field = {"ra": field.racen,
             "dec": field.deccen,
             "observatory": field.observatory.label,
             "cadence": field.cadence.label,
             "fieldID": field.field_id}

    configurations = await wrapBlocking(getConfigurations, designID)

    c_names, counts = np.unique(cartons, return_counts=True)
    targets = [{"name": n, "count": c} for n, c in zip(c_names, counts)]

    templateDict = getTemplateDictBase()
    templateDict.update({
        "designID": designID,
        "configurations": configurations,
        "targets": targets,
        "designNumber": this_d2f.exposure,
        "status": status,
        "fiberCounts": fiberCounts,
        "mjd": int(mjd),
        **field
    })

    return await render_template("designDetail.html", **templateDict)


if __name__ == "__main__":
    pass
