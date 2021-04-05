# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb

from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler, Design, Queue
from kronos.apoSite import APOSite
from kronos.dbConvenience import getRecentExps
from kronos.controllers.planObserving import mjdToHMstr, getAlmanac, backupDicts

from . import getTemplateDictBase

lookAhead_page = Blueprint("lookAhead_page", __name__)

ALLSURVEYS = ["APOGEE"]


@lookAhead_page.route('/lookAhead.html', methods=['GET', 'POST'])
async def lookAhead():

    now = Time.now()
    now.format = "mjd"
    mjd_now = now.value
    # use an offset so "tonight" is used until 15:00 UTC
    offset = 3 / 24
    mjd = round(mjd_now - offset)

    form = await request.form
    args = request.args

    redo = False

    # parse POST/GET args

    print(args)

    if "mjd" in args:
        print(int(args["mjd"]))
        mjd = int(args["mjd"])
    # if "redo" in args:
    #     # deprecated?
    #     redo = True

    # if "rmField" in form:
    #     rmField = int(form["rmField"])
    #     opsdb.Queue.rm(rmField)

    # elif "flush" in form:
    #     opsdb.Queue.flushQueue()

    # elif "redo" in form:
    #     redo = True

    # if "replace" in form:
    #     replace = int(form["replace"])
    # else:
    #     replace = False

    # if "backup" in form:
    #     replacementField = int(form["backup"])
    #     oldField = int(form["prev"])
    # else:
    #     replacementField = None

    # if "remainder" in form:
    #     redoFromField = True
    # else:
    #     redoFromField = False

    templateDict = getTemplateDictBase()

    scheduler = Scheduler(observatory="apo")

    mjd_evening_twilight, mjd_morning_twilight = scheduler.getNightBounds(mjd)

    fields, errors = scheduler.schedNoQueue(mjd_evening_twilight, mjd_morning_twilight)

    startTime = Time(mjd_evening_twilight, format="mjd").datetime
    endTime = Time(mjd_morning_twilight, format="mjd").datetime

    schedule = {
            "queriedMJD": mjd,
            "timeBarStartUTC": startTime,
            "timeBarEndUTC": endTime
        }

    queue = Queue()
    if len(queue.fields) == 0:
        viz = None
    else:
        # queue.scheduleFields(mjd_evening_twilight, mjd_morning_twilight)
        viz = ApogeeViz(schedule, queue.fields).export()

    schedViz = ApogeeViz(schedule, fields).export()

    templateDict.update({
        "apogeeViz": viz,
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
