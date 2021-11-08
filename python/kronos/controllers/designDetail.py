# -*- coding: utf-8 -*-
import asyncio

from quart import request, render_template, Blueprint

import numpy as np

from sdssdb.peewee.sdss5db import targetdb

from kronos import wrapBlocking
from kronos.dbConvenience import getConfigurations
# from kronos.scheduler import Scheduler

from . import getTemplateDictBase

designDetail_page = Blueprint("designDetail_page", __name__)


@designDetail_page.route('/designDetail.html', methods=['GET', 'POST'])
async def designDetail():

    dbField = targetdb.Field
    dbDesign = targetdb.Design

    designID = int(request.args["designID"])

    design = await wrapBlocking(dbDesign.get, designID)

    field = await wrapBlocking(dbField.get, pk=design.field.pk)

    field = {"ra": field.racen,
             "dec": field.deccen,
             "observatory": field.observatory.label,
             "cadence": field.cadence.label,
             "fieldID": field.field_id}

    configurations = await wrapBlocking(getConfigurations, designID)

    # configurations = [{"id": i,
    #                    "timeStamp": "2021-11-05T18:00:02",
    #                    "AP": 100,
    #                    "b1": 2.5,
    #                    "r1": 5.1} for i in range(3)]
    targets = [{"name": "class_" + str(i),
                "count": np.random.randint(2, 30)} for i in range(20)]

    templateDict = getTemplateDictBase()
    templateDict.update({
        "designID": designID,
        "configurations": configurations,
        "targets": targets,
        **field
    })

    return await render_template("designDetail.html", **templateDict)


if __name__ == "__main__":
    pass
