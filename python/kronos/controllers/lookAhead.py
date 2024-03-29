# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb

from kronos import wrapBlocking, observatory
from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler, Design, Queue, offsetNow
from kronos.dbConvenience import getRecentExps
from kronos.controllers.planObserving import mjdToHMstr, getAlmanac, backupDicts, summmerOrWinter

from . import getTemplateDictBase

lookAhead_page = Blueprint("lookAhead_page", __name__)

ALLSURVEYS = ["APOGEE"]


@lookAhead_page.route('/lookAhead.html', methods=['GET', 'POST'])
async def lookAhead():
    mjd = round(offsetNow())

    form = await request.form
    args = request.args

    redo = False

    # parse POST/GET args

    if "mjd" in args:
        mjd = int(args["mjd"])

    templateDict = getTemplateDictBase()

    scheduler = await wrapBlocking(Scheduler)

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, mjd)

    startTime = Time(mjd_evening_twilight, format="mjd").datetime
    endTime = Time(mjd_morning_twilight, format="mjd").datetime

    north_winter = summmerOrWinter(startTime)

    long_night = north_winter or (not north_winter and observatory == "LCO")

    if north_winter and observatory == "APO":
        long_night = True
    elif not north_winter and observatory == "LCO":
        long_night = True
    else:
        long_night = False

    if long_night:
        mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds,
                                                                        mjd,
                                                                        twilight=-12)
        startTime = Time(mjd_evening_twilight, format="mjd").datetime
        endTime = Time(mjd_morning_twilight, format="mjd").datetime

    evening_twilight_dark, morning_twilight_dark = await wrapBlocking(scheduler.getDarkBounds, mjd)

    evening_twilight_utc = Time(evening_twilight_dark, format="mjd").datetime
    morning_twilight_utc = Time(morning_twilight_dark, format="mjd").datetime

    fields, errors = await scheduler.schedNoQueue(mjd_evening_twilight, mjd_morning_twilight)

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

    queue = await wrapBlocking(Queue)
    # if len(queue.fields) == 0:
    #     viz = None
    # else:
    #     # queue.scheduleFields(mjd_evening_twilight, mjd_morning_twilight)
    #     viz = ApogeeViz(schedule, queue.fields).export()

    schedViz = await ApogeeViz(schedule, fields).export()

    almanac = getAlmanac(mjd)

    templateDict.update({
        "apogeeViz": None,
        "schedViz": schedViz,
        "mjd": mjd,
        "errorMsg": [],
        "almanac": (*almanac, brightDark),
        "queue": queue.designs,
        "backups": []
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("lookAhead.html", **templateDict)


if __name__ == "__main__":
    pass
