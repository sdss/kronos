# -*- coding: utf-8 -*-
import asyncio
from collections import defaultdict
import datetime

import numpy as np
from astropy.time import Time
from peewee import DoesNotExist

from quart import request, render_template, Blueprint

from kronos import wrapBlocking
from kronos.dbConvenience import getField, fieldIdToPks
from kronos.scheduler import Scheduler

from . import getTemplateDictBase

fieldDetail_page = Blueprint("fieldDetail_page", __name__)


def designsToEpoch(mjd_design=None, cadence_nexps=None,
                   cadence_max_length=None, **kwargs):
    designs = [d for d in mjd_design.keys()]
    designs.sort()

    if len(designs) == 0:
        return []

    assert designs[-1] - designs[0] == len(designs) - 1, "designs observed out of order"

    expCount = [np.sum(cadence_nexps[:i+1]) for i in range(len(cadence_nexps))]

    epochs = list()

    for i, end in enumerate(expCount):
        if i == 0:
            start = 0
        else:
            start = expCount[i-1]
        # end is index + 1 because it starts at 1 since it's N exp
        # and slices that don't exist will just be empty! love python
        epochs.append(designs[start:end])

    epoch_sn = list()
    for des, length in zip(epochs, cadence_max_length):
        if len(des) == 0:
            continue
        if len(des) == 1:
            label = str(des[0])
        else:
            label = f"{des[0]}-{des[-1]}"
        theseDesigns = [mjd_design[d] for d in des]
        mjds = list()
        for d in theseDesigns:
            mjds.extend([k for k in d.keys()])
        end = np.max(mjds)
        start = end - length
        out = {"label": label, "mjd": int(end), "r1": 0, "b1": 0, "AP": 0}
        for mjds in theseDesigns:
            for mjd in mjds:
                if mjd >= start:
                    out["r1"] += mjds[mjd]["r1"]
                    out["b1"] += mjds[mjd]["b1"]
                    out["AP"] += mjds[mjd]["AP"]
        epoch_sn.append(out)

    return epoch_sn


@fieldDetail_page.route('/fieldDetail.html', methods=['GET', 'POST'])
async def fieldDetail():

    fieldID = int(request.args["fieldID"])

    templateDict = getTemplateDictBase()

    if "pk" in request.args:
        pk = int(request.args["pk"])
    else:
        pks, cads = await wrapBlocking(fieldIdToPks, fieldID)
        if len(pks) == 0:
            return await render_template('404.html'), 404
        elif len(pks) == 2:
            templateDict.update({"fieldID": fieldID, "pks": pks, "cadences": cads})
            return await render_template('disambiguateFieldID.html', **templateDict)
        else:
            pk = pks[0]

    if "mjd" in request.args:
        mjd = float(request.args["mjd"])
        offset = 3 / 24
        mjd_int = round(mjd - offset)
    else:
        mjd = None

    if mjd is None:
        now = Time.now()
        now.format = "mjd"
        mjd = now.value
        # use an offset so "tonight" is used until 15:00 UTC
        offset = 3 / 24
        mjd_int = round(mjd - offset)

    # grab a dict of field params, ra, dec, observatory, and cadence at least
    # all necessary calls should be done inside getField funct so wrap here
    try:
        field = await wrapBlocking(getField, pk)
    except DoesNotExist:
        return await render_template('404.html'), 404

    errors = list()
    try:
        epochSN = designsToEpoch(**field)
    except AssertionError:
        epochSN = list()
        errors.append("Designs observed out of order, no epochs for you")

    # kronos scheduler
    scheduler = await wrapBlocking(Scheduler)

    # roboscheduler scheduler
    RS = scheduler.scheduler

    ra = np.arange(0, 360, 5)
    dec = np.arange(-90, 90, 5)

    ras, decs = np.meshgrid(ra, dec)

    ras = ras.flatten()
    decs = decs.flatten()

    mjd_evening_twilight, mjd_morning_twilight = await wrapBlocking(scheduler.getNightBounds, mjd_int)

    if mjd < mjd_evening_twilight or mjd > mjd_morning_twilight:
        mjd = mjd_evening_twilight
        start_idx = 0
        errors.append("MJD not during night, using evening twilight")
    else:
        mjd = mjd - 4/24
        start_idx = 4

    while mjd - mjd_evening_twilight > 1/24:
        await asyncio.sleep(0)
        mjd -= 1/24
        start_idx -= 1
    if start_idx < 0:
        start_idx = 0
    mjds = mjd + np.arange(0, 0.5, 1/24)

    skies = list()
    times = list()  # because I don't want to do that in JS

    for m in mjds:
        await asyncio.sleep(0)
        moon_pos = RS.moon_radec(mjd=m)
        lunar_phase = float(RS.moon_illumination(mjd=m))
        malt, maz = RS.radec2altaz(mjd=m, ra=moon_pos[0], dec=moon_pos[1])

        talt, taz = RS.radec2altaz(mjd=m, ra=ras, dec=decs)

        horizon = np.where(talt > 0)
        talt = talt[horizon]
        taz = taz[horizon]

        m_ras = ras[horizon]
        m_decs = decs[horizon]

        delta = RS.deltaV_sky_pos(m, m_ras, m_decs)

        fra = field["ra"]
        fdec = field["dec"]
        falt, faz = RS.radec2altaz(mjd=m, ra=fra, dec=fdec)

        t = Time(m, format="mjd")
        t.format = "iso"
        t = t.datetime
        ut = "{:2d}/{:02d} {:2d}:{:02d}".format(t.month, t.day, t.hour, t.minute)
        times.append(ut)

        ks91 = {"mjd": m,
                "time": ut,
                "malt": float(malt),
                "maz": float(maz),
                "phase": lunar_phase,
                "skies": [{"alt": a,
                           "az": z,
                           "delta": d} for a, z, d in zip(talt, taz, delta)],
                "dmin": float(np.min(delta)),
                "dmax": float(np.max(delta)),
                "falt": float(falt),
                "faz": float(faz)
                }
        skies.append(ks91)

    templateDict.update({
        "fieldID": fieldID,
        "skies": skies,
        "times": times,
        "start_idx": start_idx,
        "errorMsg": errors,
        "epochSN": epochSN,
        **field
    })

    return await render_template("fieldDetail.html", **templateDict)


if __name__ == "__main__":
    pass
