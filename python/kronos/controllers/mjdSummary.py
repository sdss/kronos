# -*- coding: utf-8 -*-
import asyncio
import requests
from datetime import datetime

import yaml
from quart import request, render_template, Blueprint
from astropy.time import Time

from kronos import wrapBlocking
from kronos.dbConvenience import getFieldsTimeRange, fetchMjds
from kronos.scheduler import offsetNow, Scheduler

from . import getTemplateDictBase


# def trackIPs(ip, city):
#     now = datetime.now().strftime("%Y-%m-%d")
#     with open("/data/logs/roboscheduler/summaryTracking.yml", "r") as log:
#         tracking = yaml.load(log, Loader=yaml.FullLoader)
#     if ip in tracking:
#         tracking[ip]["N"] += 1
#         tracking[ip]["latest"] = now
#     else:
#         tracking[ip] = {"city": city, "N": 1, "latest": now}
#     with open("/data/logs/roboscheduler/summaryTracking.yml", "w") as log:
#         print(yaml.dump(tracking), file=log)
#     return tracking


mjdSummary_page = Blueprint("mjdSummary_page", __name__)


@mjdSummary_page.route('/mjdSummary/', defaults={'mjd': None})
@mjdSummary_page.route('/mjdSummary/<int:mjd>', methods=['GET'])
async def mjdSummary(mjd):

    templateDict = getTemplateDictBase()

    # remote_ip = request.headers["Remote-Addr"]
    # # if remote_ip != "127.0.0.1":
    # url = f"https://geolocation-db.com/json/{remote_ip}"
    # response = await wrapBlocking(requests.get, url)
    # city = response.json()["city"]

    # tracking = await wrapBlocking(trackIPs, remote_ip, city)

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
