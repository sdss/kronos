# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

from quart import request, render_template, Blueprint

from astropy.time import Time, TimeDelta

from kronos.vizWindow import ApogeeViz
from kronos.scheduler import Scheduler

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
            ("Sidereal Time at Midnight","99:00 LST"),
            ("Moon Illumination", "{:4.2f}".format(float(RS.moon_illumination(mjd=mjd)))),
            ("Moonrise", "?"),
            ("Moonset", "?"),
        )
    )
    return twilights, headers, other


@planObserving_page.route('/planObserving.html', methods=['GET', 'POST'])
async def planObserving():

    now = Time.now()
    now.format = "mjd"
    mjd = round(now.value)

    if request.method == "POST":

        mjd = int(request.form.get("newMJD", 59060))

    templateDict = getTemplateDictBase()
    # date = datetime.datetime.utcnow()
    # date = datetimenow.date()
    scheduler = Scheduler(observatory="apo", base="beta-5")

    fields, startTime, endTime = scheduler.scheduleMjd(mjd)

    schedule = {
            "queriedMJD": mjd,
            "timeBarStartUTC": startTime,
            "timeBarEndUTC": endTime
        }

    # print(ApogeeViz(schedule, fields).export())

    templateDict.update({
        # "apogeeViz": ApogeeViz(schedule, apogeePlateList).export() if apogeePlateList else None,
        "apogeeViz": ApogeeViz(schedule, fields).export(),   
        "mjd": mjd,
        "errorMsg": [],  # + ", ".join(["autoscheduler error: " + x for x in autoscheduler.queryResult["errors"]]),
        "almanac": getAlmanac(mjd),  # if schedule else None,
        "activeCartList": [],
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("planObserving.html", **templateDict)


if __name__ == "__main__":
    pass
