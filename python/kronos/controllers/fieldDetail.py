# -*- coding: utf-8 -*-
import asyncio
from collections import defaultdict
import datetime

import numpy as np
from astropy.time import Time
from peewee import DoesNotExist

from quart import request, render_template, Blueprint

from sdssdb.peewee.sdss5db import opsdb, targetdb

from kronos import wrapBlocking
from kronos.dbConvenience import getField, fieldIdToPks
from kronos.scheduler import Scheduler
from kronos.designCompletion import checker

from . import getTemplateDictBase

fieldDetail_page = Blueprint("fieldDetail_page", __name__)


def designsToEpoch(mjd_design=None, cadence_nexps=None,
                   cadence_max_length=None, boss_count=None,
                   mjd_exposure=None, ap_count=None, **kwargs):
    designs = [d for d in mjd_design.keys()]
    # designs.sort()

    if len(designs) == 0:
        return [], None

    # assert designs[-1] - designs[0] == len(designs) - 1, "designs observed out of order"
    first = np.min(designs)
    last = np.max(designs)

    designs = [i for i in range(first, last+1)]

    expCount = [np.sum(cadence_nexps[:i+1]) for i in range(len(cadence_nexps))]

    epochs = list()

    for i, end in enumerate(expCount):
        if i == 0:
            start = 0
        else:
            start = expCount[i-1]
        # end is index + 1 because it starts at 1 since it's N exp

        epoch_designs = [d for d in designs[start:end] if d in mjd_design]

        # and slices that don't exist will just be empty! love python
        epochs.append(epoch_designs)

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
        epoch_count = 0
        for d_id in des:
            if boss_count.get(d_id, 0):
                epoch_count += boss_count.get(d_id, 0)
            else:
                epoch_count += ap_count.get(d_id, 0)
        out = {"label": label, "mjd": int(end),
               "r_camera": 0, "b_camera": 0, "AP": 0,
               "epoch_count": epoch_count,
               "exposures": [], "mjds": []}
        for mjds in theseDesigns:
            for mjd in mjds:
                if mjd >= start:
                    out["r_camera"] += mjds[mjd]["r_camera"]
                    out["b_camera"] += mjds[mjd]["b_camera"]
                    out["AP"] += mjds[mjd]["AP"]
                    out["exposures"].extend(mjd_exposure[mjd])
                    if mjd not in out["mjds"]:
                        out["mjds"].append(mjd)
        end_mjd = np.min(out["mjds"]) + length
        end_time = Time(end_mjd, format="mjd")
        out["last_chance"] = end_time.datetime.strftime("%Y/%m/%d, %H:%M")
        epoch_sn.append(out)

    if len(epoch_sn) > 0:
        # find last design of last epoch
        last_design = first + expCount[len(epoch_sn) - 1] - 1
    else:
        last_design = None

    return epoch_sn, last_design


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
        elif len(pks) > 1:
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
    last_design = None
    try:
        epochSN, last_design = designsToEpoch(**field)
    except AssertionError:
        epochSN = list()
        errors.append("Designs observed out of order, no epochs for you")

    if len(epochSN) > 0:
        last_chance = epochSN[-1]["last_chance"]
    else:
        last_chance = None

    d2s = opsdb.DesignToStatus
    status = opsdb.CompletionStatus
    design = targetdb.Design

    if last_design:
        stats_query = await wrapBlocking(d2s.select(status.label,
                                                    design.design_mode_label)\
                                            .join(status)
                                            .switch(d2s)
                                            .join(design)
                                            .where(d2s.design_id == last_design)
                                            .get)

        last_status = stats_query.status.label
        if last_status != "done":
            last_design_mode = stats_query.design.design_mode.label
        else:
            last_design_mode = None
            last_chance = None
    else:
        last_status = "not started"
        last_design_mode = None

    if last_design_mode in checker.keys():
        n_exp = 1
        if last_design_mode == "dark_faint":
            try:
                n_exp = int(field["cadence"].split("_")[-2].split("x")[-1])
            except:
                errors.append("dark faint error, S/N goals may be inaccurate")
        mode_checker = checker[last_design_mode]
        if mode_checker.epoch_bSN2 is None:
            mode_checker.epoch_rSN2 = 0
            mode_checker.epoch_bSN2 = 0
        sn_reqs = {"AP": mode_checker.epoch_apSN2,
                   "R": mode_checker.epoch_rSN2*n_exp,
                   "B": mode_checker.epoch_bSN2*n_exp}
    else:
        sn_reqs = {"AP": 0,
                   "R": 0,
                   "B": 0}

    f2p = opsdb.FieldToPriority
    fp = opsdb.FieldPriority

    pr_query = await wrapBlocking(f2p.select(fp.label)
                                     .join(fp)
                                     .where(f2p.field == pk)
                                     .get_or_none)
    if pr_query:
        priority = pr_query.FieldPriority.label
    else:
        priority = None

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
        "done_status": last_status,
        "priority": priority,
        "sn_reqs": sn_reqs,
        "last_chance": last_chance,
        **field
    })

    return await render_template("fieldDetail.html", **templateDict)


if __name__ == "__main__":
    pass
