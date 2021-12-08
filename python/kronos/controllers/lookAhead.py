# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb

from kronos import wrapBlocking
from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler, Design, Queue, offsetNow
from kronos.dbConvenience import getRecentExps
from kronos.controllers.planObserving import mjdToHMstr, getAlmanac, backupDicts

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

    fields, errors = await scheduler.schedNoQueue(mjd_evening_twilight, mjd_morning_twilight)

    startTime = Time(mjd_evening_twilight, format="mjd").datetime
    endTime = Time(mjd_morning_twilight, format="mjd").datetime

    schedule = {
            "queriedMJD": mjd,
            "timeBarStartUTC": startTime,
            "timeBarEndUTC": endTime
        }

    queue = await wrapBlocking(Queue)
    # if len(queue.fields) == 0:
    #     viz = None
    # else:
    #     # queue.scheduleFields(mjd_evening_twilight, mjd_morning_twilight)
    #     viz = ApogeeViz(schedule, queue.fields).export()

    schedViz = await ApogeeViz(schedule, fields).export()

    templateDict.update({
        "apogeeViz": None,
        "schedViz": schedViz,
        "mjd": mjd,
        "errorMsg": [],
        "almanac": getAlmanac(mjd),  # if schedule else None,
        "queue": queue.designs,
        "backups": []
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("lookAhead.html", **templateDict)


if __name__ == "__main__":
    pass
