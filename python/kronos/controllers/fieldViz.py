# -*- coding: utf-8 -*-
import asyncio
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb

from kronos import wrapBlocking
from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler, offsetNow, DesignList
from kronos.controllers.planObserving import getAlmanac

from . import getTemplateDictBase

fieldViz_page = Blueprint("fieldViz_page", __name__)

ALLSURVEYS = ["APOGEE"]


@fieldViz_page.route('/fieldViz.html', methods=['GET', 'POST'])
async def fieldViz():
    mjd = round(offsetNow())

    # now = Time.now()
    # now.format = "mjd"
    # mjd_now = now.value

    form = await request.form

    errors = list()

    if "mjd" in form:
        if len(form["mjd"].strip()) > 0:
            try:
                mjd = int(form["mjd"])
            except:
                errors.append("invalid mjd input")
                design_ids = list()
    if "designs" in form:
        d_text = form["designs"]
        try:
            if "," in d_text:
                design_ids = [int(d) for d in d_text.strip().split(",") if len(d)]
            else:
                design_ids = [int(d_text)]
        except:
            errors.append("invalid design input")
            design_ids = list()
    else:
        design_ids = list()

    templateDict = getTemplateDictBase()

    scheduler = await wrapBlocking(Scheduler)

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, mjd)

    startTime = Time(mjd_evening_twilight, format="mjd").datetime
    endTime = Time(mjd_morning_twilight, format="mjd").datetime

    evening_twilight_dark, morning_twilight_dark = await wrapBlocking(scheduler.getDarkBounds, mjd)

    evening_twilight_utc = Time(evening_twilight_dark, format="mjd").datetime
    morning_twilight_utc = Time(morning_twilight_dark, format="mjd").datetime

    schedule = {
            "queriedMJD": mjd,
            "timeBarStartUTC": startTime,
            "timeBarEndUTC": endTime,
            "eveningTwilightUTC": evening_twilight_utc,
            "morningTwilightUTC": morning_twilight_utc
        }

    evening_twilight_dark, morning_twilight_dark = await wrapBlocking(scheduler.getDarkBounds, mjd)

    brightDark = scheduler.nightSchedule(evening_twilight_dark, morning_twilight_dark)

    schedule.update(**brightDark)

    for k, v in brightDark.items():
        if v is None:
            continue
        brightDark[k] = v.strftime("%H:%M")

    mean = (mjd_evening_twilight + mjd_morning_twilight) / 2

    designList = await wrapBlocking(DesignList, design_ids=design_ids, mjd=mean)
    if len(designList.fields) == 0:
        viz = None
    else:
        viz = await ApogeeViz(schedule, designList.fields, useDesign=True).export()

    almanac = await wrapBlocking(getAlmanac, mjd)

    if viz is not None:
        for r in viz["allRows"]:
            for v in r["vizWindows"]:
                if v["primary"]:
                    v["opacity"] = 0

    templateDict.update({
        "apogeeViz": viz,
        "mjd": mjd,
        "errorMsg": errors,
        "almanac": (*almanac, brightDark),  # if schedule else None
        "designs": design_ids,
        "mjd": mjd
    })

    return await render_template("fieldViz.html", **templateDict)


if __name__ == "__main__":
    pass
