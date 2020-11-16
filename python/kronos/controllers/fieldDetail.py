# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint


from . import getTemplateDictBase

fieldDetail_page = Blueprint("fieldDetail_page", __name__)


@fieldDetail_page.route('/fieldDetail.html', methods=['GET', 'POST'])
async def fieldDetail():

    if "fieldID" in request.args:
        fieldID = int(request.args["fieldID"])

    templateDict = getTemplateDictBase()

    templateDict.update({
        "fieldID": fieldID
    })

    return await render_template("fieldDetail.html", **templateDict)


if __name__ == "__main__":
    pass
