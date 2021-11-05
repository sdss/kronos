# -*- coding: utf-8 -*-
import asyncio

from quart import request, render_template, Blueprint

import numpy as np

from kronos import wrapBlocking
# from kronos.dbConvenience import getField
# from kronos.scheduler import Scheduler

from . import getTemplateDictBase

designDetail_page = Blueprint("designDetail_page", __name__)


@designDetail_page.route('/designDetail.html', methods=['GET', 'POST'])
async def designDetail():

    if "designID" in request.args:
        designID = int(request.args["designID"])

    # grab a dict of field params, ra, dec, observatory, and cadence at least
    # all necessary calls should be done inside getField funct so wrap here
    # field = await wrapBlocking(getField, fieldID)
    field = {"ra": 1, "dec": 2,
             "observatory": "apo",
             "cadence": "yes",
             "fieldID": 5}
    templateDict = getTemplateDictBase()

    configurations = [{"id": i,
                       "timeStamp": "2021-11-05T18:00:02",
                       "AP": 100,
                       "b1": 2.5,
                       "r1": 5.1} for i in range(3)]
    targets = [{"name": "class_" + str(i),
               "count": np.random.randint(2, 30)} for i in range(20)]

    templateDict.update({
        "designID": designID,
        "configurations": configurations,
        "targets": targets,
        **field
    })

    return await render_template("designDetail.html", **templateDict)


if __name__ == "__main__":
    pass
