# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime

import numpy as np
from astropy.time import Time

from quart import request, render_template, Blueprint

from kronos import wrapBlocking
from kronos.dbConvenience import getField
from kronos.scheduler import Scheduler

from . import getTemplateDictBase

fieldDetail_page = Blueprint("fieldDetail_page", __name__)


@fieldDetail_page.route('/fieldDetail.html', methods=['GET', 'POST'])
async def fieldDetail():

    if "fieldID" in request.args:
        fieldID = int(request.args["fieldID"])

    if "mjd" in request.args:
        mjd = int(request.args["mjd"])
    else:
        mjd = None

    if mjd is None:
        now = Time.now()
        now.format = "mjd"
        mjd_now = now.value
        # use an offset so "tonight" is used until 15:00 UTC
        offset = 3 / 24
        mjd = round(mjd_now - offset)

    # grab a dict of field params, ra, dec, observatory, and cadence at least
    # all necessary calls should be done inside getField funct so wrap here
    field = await wrapBlocking(getField, fieldID)

    RS = Scheduler().scheduler

    ra = np.arange(0, 360, 5)
    dec = np.arange(-60, 90, 5)

    ras, decs = np.meshgrid(ra, dec)

    ras = ras.flatten()
    decs = decs.flatten()

    moon_pos = RS.moon_radec(mjd=mjd)
    lunar_phase = float(RS.moon_illumination(mjd=mjd))

    malt, maz = RS.radec2altaz(mjd=mjd, ra=moon_pos[0], dec=moon_pos[1])
    talt, taz = RS.radec2altaz(mjd=mjd, ra=ras, dec=decs)

    horizon = np.where(talt > 0)
    talt = talt[horizon]
    taz = taz[horizon]

    ras = ras[horizon]
    decs = decs[horizon]

    delta = RS.deltaV_sky_pos(mjd, ras, decs)

    fra = field["ra"]
    fdec = field["dec"]
    falt, faz = RS.radec2altaz(mjd=mjd, ra=fra, dec=fdec)

    ks91 = {"mjd": mjd,
            "malt": float(malt),
            "maz": float(maz),
            "phase": lunar_phase,
            "skies": [{"alt": a,
                       "az": z,
                       "delta": d} for a, z, d in zip (talt, taz, delta)],
            "dmin": float(np.min(delta)),
            "dmax": float(np.max(delta)),
            "falt": float(falt),
            "faz": float(faz)
            }

    templateDict = getTemplateDictBase()

    templateDict.update({
        "fieldID": fieldID,
        "ks91": ks91,
        **field
    })

    return await render_template("fieldDetail.html", **templateDict)


if __name__ == "__main__":
    pass
