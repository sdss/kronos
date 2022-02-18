#!/usr/bin/env/python

from quart import Blueprint, request, jsonify

from kronos import wrapBlocking
from kronos.dbConvenience import getRecentExps, designCompletion, queueLength, apql

dbEndPoints = Blueprint("dbEndPoints", __name__)


@dbEndPoints.route('/recentExposures/<int:mjd>', methods=['GET'])
async def recentExposures(mjd):
    exps = await wrapBlocking(getRecentExps, mjd)

    return jsonify(exps)


@dbEndPoints.route('/designCompletion/', methods=["GET"])
async def getDesignCompletion():
    if "designs" not in request.args:
        return jsonify([])
    d_text = request.args["designs"]
    try:
        if "," in d_text:
            design_ids = [int(d) for d in d_text.strip().split(",") if len(d)]
        else:
            design_ids = [int(d_text)]
    except:
        return jsonify([])
    status = await wrapBlocking(designCompletion, design_ids)

    return jsonify(status)


@dbEndPoints.route('/currentQueueLength/')
async def currentQueueLength():
    qLength = await wrapBlocking(queueLength)

    return jsonify(qLength)


@dbEndPoints.route('/latestAPQL/')
async def grabAPQR():
    ql = await wrapBlocking(apql)

    return jsonify(ql)
