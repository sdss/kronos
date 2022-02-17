# -*- coding: utf-8 -*-
import asyncio
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb

from kronos import wrapBlocking
from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler, Design, Queue, offsetNow
from kronos.site import Site
from kronos.dbConvenience import getRecentExps

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

    moon_rise, moon_set = Site.moonRiseSet(evening_mjds[0])

    other = OrderedDict(
        (
            ("Moon Illumination", "{:4.2f}".format(float(RS.moon_illumination(mjd=mjd)))),
            ("Moonrise", "{:2d}/{:02d} {:2d}:{:02d}".format(moon_rise.month, moon_rise.day,
                                                            moon_rise.hour, moon_rise.minute)),
            ("Moonset", "{:2d}/{:02d} {:2d}:{:02d}".format(moon_set.month, moon_set.day,
                                                            moon_set.hour, moon_set.minute)),
        )
    )
    return twilights, headers, other


async def backupDicts(*args, sched=None, mjd=None, prev=None):
    backup = list()
    for field_id, coord, field_pk in zip(*args):
        await asyncio.sleep(0)
        alt, az = sched.scheduler.radec2altaz(mjd=mjd, ra=coord[0], dec=coord[1])
        lst = sched.scheduler.lst(mjd=mjd)
        ha = sched.scheduler.ralst2ha(ra=coord[0], lst=lst)
        backup.append({"field_id": int(field_id),
                       "field_pk": int(field_pk),
                       "alt": float(alt),
                       "az": float(az),
                       "trueHA": float(ha),
                       "dec": float(coord[1]),
                       "selected": False,
                       "expanded": True,
                       "color": "#FF0000",
                       "prev": prev})
    return backup


@planObserving_page.route('/planObserving.html', methods=['GET', 'POST'])
async def planObserving():
    mjd = round(offsetNow())

    now = Time.now()
    now.format = "mjd"
    mjd_now = now.value

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
        await wrapBlocking(opsdb.Queue.rm, rmField)

    elif "flush" in form:
        await wrapBlocking(opsdb.Queue.flushQueue)

    elif "redo" in form:
        redo = True

    if "replace" in form:
        replace = int(form["replace"])
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

    errors = list()

    templateDict = getTemplateDictBase()
    # date = datetime.datetime.utcnow()
    # date = datetimenow.date()
    scheduler = await wrapBlocking(Scheduler)

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, mjd)

    if mjd_morning_twilight - mjd_now < 1 / 24 / 2:  # 30 minutes
        # Night's basically over, we're doing tomorrow
        errors.append("END OF NIGHT. Scheduling tomorrow")
        mjd += 1
        mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, mjd)

    startTime = Time(mjd_evening_twilight, format="mjd").datetime
    endTime = Time(mjd_morning_twilight, format="mjd").datetime

    evening_twilight_dark, morning_twilight_dark = await wrapBlocking(scheduler.getDarkBounds, mjd)

    evening_twilight_utc = Time(evening_twilight_dark, format="mjd").datetime
    morning_twilight_utc = Time(morning_twilight_dark, format="mjd").datetime

    if replacementField is not None:
        # replacing a field
        if redoFromField:
            # is it bad enough to redo the rest of the queue?
            errors.append(await scheduler.rescheduleAfterField(replacementField, mjd_morning_twilight))
        else:
            # ok just the one then!
            await scheduler.replaceField(oldField, replacementField)

    if redo:
        # clear the queue
        await wrapBlocking(opsdb.Queue.flushQueue)
        # redo the whole queue, but check if it's during the night

        winter = evening_twilight_utc.month < 3
        if not winter and evening_twilight_utc.month < 4:
            winter = evening_twilight_utc.day < 20
        fall = evening_twilight_utc.month > 10
        if not fall and evening_twilight_utc.month > 9:
            fall = evening_twilight_utc.day > 22

        if winter or fall:
            # either before 3/20 or after 9/22
            mjd_evening_twilight = evening_twilight_dark
            mjd_morning_twilight = morning_twilight_dark

        if mjd_now > mjd_evening_twilight:
            start_mjd = mjd_now
        else:
            start_mjd = mjd_evening_twilight
        errors.append(await scheduler.queueFromSched(start_mjd, mjd_morning_twilight))

    schedule = {
            "queriedMJD": mjd,
            "timeBarStartUTC": startTime,
            "timeBarEndUTC": endTime,
            "eveningTwilightUTC": evening_twilight_utc,
            "morningTwilightUTC": morning_twilight_utc
        }

    queue = await wrapBlocking(Queue)
    if len(queue.fields) == 0:
        viz = None
    else:
        # queue.scheduleFields(mjd_evening_twilight, mjd_morning_twilight)
        viz = await ApogeeViz(schedule, queue.fields).export()

    if replace:
        # make replace the fieldID to be replaced, or False
        field = queue.fieldDict[replace]
        args = await scheduler.choiceFields(field.startTime, exp=len(field.designs),
                                            oldPos=[field.ra, field.dec])
        # backups = await backupDicts(*args, sched=scheduler, mjd=field.startTime,
        #                             prev=replace)
        backups = await backupDicts(*args, sched=scheduler, mjd=mjd_now,
                                    prev=replace)
        # for f in viz["plateRows"]:
        #     if f["fieldID"] == field.fieldID:
        #         for k in ["mjd_start", "dec", "tableItems", "trueHA"]:
        #             print(f["fieldID"], k, f[k])
    else:
        backups = list()

    exps = await wrapBlocking(getRecentExps, mjd)

    almanac = await wrapBlocking(getAlmanac, mjd)

    templateDict.update({
        # "apogeeViz": ApogeeViz(schedule, apogeePlateList).export() if apogeePlateList else None,
        "apogeeViz": viz,
        "mjd": mjd,
        "almanac": almanac,  # if schedule else None,
        "queue": queue.designs,
        "backups": backups,
        "exposures": exps,
        "errorMsg": errors
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("planObserving.html", **templateDict)


if __name__ == "__main__":
    pass
