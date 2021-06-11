# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from kronos import wrapBlocking
from kronos.dbConvenience import getField

from . import getTemplateDictBase

fieldDetail_page = Blueprint("fieldDetail_page", __name__)


@fieldDetail_page.route('/fieldDetail.html', methods=['GET', 'POST'])
async def fieldDetail():

    if "fieldID" in request.args:
        fieldID = int(request.args["fieldID"])

    # grab a dict of field params, ra, dec, observatory, and cadence at least
    # all necessary calls should be done inside getField funct so wrap here
    field = await wrapBlocking(getField, fieldID)

    templateDict = getTemplateDictBase()

    templateDict.update({
        "fieldID": fieldID,
        **field
    })

    return await render_template("fieldDetail.html", **templateDict)


if __name__ == "__main__":
    pass
