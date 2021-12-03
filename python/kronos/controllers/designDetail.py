# -*- coding: utf-8 -*-
import asyncio

from quart import request, render_template, Blueprint

import numpy as np

from sdssdb.peewee.sdss5db import targetdb

from kronos import wrapBlocking
from kronos.dbConvenience import getConfigurations, designDetails
# from kronos.scheduler import Scheduler

from . import getTemplateDictBase

designDetail_page = Blueprint("designDetail_page", __name__)


@designDetail_page.route('/designDetail.html', methods=['GET', 'POST'])
async def designDetail():

    dbField = targetdb.Field
    dbDesign = targetdb.Design

    designID = int(request.args["designID"])

    design = await wrapBlocking(dbDesign.get, designID)

    status, cartons = await wrapBlocking(designDetails, design)

    field = await wrapBlocking(dbField.get, pk=design.field.pk)

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
        "designNumber": design.exposure,
        "status": status,
        **field
    })

    return await render_template("designDetail.html", **templateDict)


if __name__ == "__main__":
    pass
