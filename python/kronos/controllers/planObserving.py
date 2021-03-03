# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time, TimeDelta

from sdssdb.peewee.sdss5db import opsdb

from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler, Design, Queue

from . import getTemplateDictBase

planObserving_page = Blueprint("planObserving_page", __name__)

ALLSURVEYS = ["APOGEE"]


def mjdToHMstr(mjd):
    time = Time(mjd, format="mjd")
    time.format = "datetime"
    return "{:02d}:{:02d}".format(time.datetime.hour, time.datetime.minute)


def getAlmanac(mjd):
    """Return a dictionary (with nicely formatted values)
    for displaying site info for a given date (datetime)
    """
    RS = Scheduler().scheduler

    headers = ("sunset", "8 deg", "12 deg", "15 deg", "18 deg", "18 deg", "15 deg", "12 deg", "8 deg", "sunrise")
    angles = [0, -8, -12, -15, -18]
    evening_mjds = [RS.evening_twilight(mjd=mjd, twilight=a) for a in angles]
    evening_times = [mjdToHMstr(m) for m in evening_mjds]
    angles.reverse()
    morning_mjds = [RS.morning_twilight(mjd=mjd, twilight=a) for a in angles]
    morning_times = [mjdToHMstr(m) for m in morning_mjds]
    twilights = evening_times + morning_times
    other = OrderedDict(
        (
            ("Sidereal Time at Midnight", "99:00 LST"),
            ("Moon Illumination", "{:4.2f}".format(float(RS.moon_illumination(mjd=mjd)))),
            ("Moonrise", "?"),
            ("Moonset", "?"),
        )
    )
    return twilights, headers, other


def backupDicts(*args, sched=None, mjd=None, prev=None):
    backup = list()
    for field, coord in zip(*args):
        alt, az = sched.scheduler.radec2altaz(mjd=mjd, ra=coord[0], dec=coord[1])
        backup.append({"field": int(field),
                       "alt": float(alt),
                       "az": float(az),
                       "selected": False,
                       "expanded": True,
                       "color": "#FF0000",
                       "prev": prev})
    return backup

@planObserving_page.route('/planObserving.html', methods=['GET', 'POST'])
async def planObserving():

    now = Time.now()
    now.format = "mjd"
    mjd = round(now.value)

    form = await request.form
    args = request.args

    redo = False

    # parse POST/GET args

    if "mjd" in args:
        # deprecated?
        mjd = int(args["mjd"])
        redo = True
    if "redo" in args:
        # deprecated?
        redo = True

    if "rmField" in form:
        rmField = int(form["rmField"])
        opsdb.Queue.rm(rmField)

    elif "flush" in form:
        opsdb.Queue.flushQueue()

    elif "redo" in form:
        redo = True

    if "replace" in form:
        replace = form["replace"]
    else:
        replace = False

    if "backup" in form:
        replacementField = int(form["backup"])
        oldField = int(form["prev"])
    else:
        replacementField = None

    if "remainder" in form:
        redoFromField = True
    else:
        redoFromField = False

    templateDict = getTemplateDictBase()
    # date = datetime.datetime.utcnow()
    # date = datetimenow.date()
    scheduler = Scheduler(observatory="apo")

    if replacementField is not None:
        scheduler.replaceField(oldField, replacementField)

    # fields, startTime, endTime = scheduler.scheduleMjd(mjd)

    mjd_evening_twilight, mjd_morning_twilight = scheduler.scheduleMjd(mjd,
                                                                       redo=redo)

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

    if replace:
        # make replace the new field, or False
        field = queue.fields[[f.fieldID for f in queue.fields] == replace]
        args = scheduler.choiceFields(field.startTime)
        backups = backupDicts(*args, sched=scheduler, mjd=field.startTime,
                              prev=replace)
    else:
        backups = list()

    templateDict.update({
        # "apogeeViz": ApogeeViz(schedule, apogeePlateList).export() if apogeePlateList else None,
        "apogeeViz": viz,
        "mjd": mjd,
        "errorMsg": [],  # + ", ".join(["autoscheduler error: " + x for x in autoscheduler.queryResult["errors"]]),
        "almanac": getAlmanac(mjd),  # if schedule else None,
        "queue": queue.designs,
        "backups": backups
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("planObserving.html", **templateDict)


if __name__ == "__main__":
    pass
