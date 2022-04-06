# -*- coding: utf-8 -*-
import asyncio

from quart import request, render_template, Blueprint
from astropy.time import Time

from kronos import wrapBlocking
from kronos.dbConvenience import getFieldsTimeRange, fetchMjds
from kronos.scheduler import offsetNow, Scheduler

from . import getTemplateDictBase

mjdSummary_page = Blueprint("mjdSummary_page", __name__)


@mjdSummary_page.route('/mjdSummary/', defaults={'mjd': None})
@mjdSummary_page.route('/mjdSummary/<int:mjd>', methods=['GET'])
async def mjdSummary(mjd):

    templateDict = getTemplateDictBase()

    if "mjd" in request.args:
        mjd = float(request.args["mjd"])
    # else:
    #     mjd = offsetNow()

    if mjd is None:
        mjd = offsetNow()

    scheduler = await wrapBlocking(Scheduler)

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, round(mjd))
    mjd = round(mjd_evening_twilight)
    start = Time(mjd_evening_twilight, format="mjd").datetime
    end = Time(mjd_morning_twilight, format="mjd").datetime

    errors = list()
    fields = await wrapBlocking(getFieldsTimeRange, start, end)
    mjds = await wrapBlocking(fetchMjds)

    templateDict.update({
        "errorMsg": errors,
        "fields": fields,
        "mjd": mjd,
        "mjds": mjds
    })

    return await render_template("mjdSummary.html", **templateDict)


if __name__ == "__main__":
    pass
