#!/usr/bin/env/python

from quart import Blueprint, request, jsonify

from kronos import wrapBlocking
from kronos.dbConvenience import (getRecentExps, designCompletion,
                                  queueLength, getDesignStatus,
                                  apql, modifyDesignStatus,
                                  getField, latestFieldID)
from kronos.controllers.fieldDetail import designsToEpoch


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


@dbEndPoints.route('/manualDesignCompletion/', methods=["GET"])
async def manualDesignCompletion():
    design_id = int(request.args["design_id"])
    status = request.args["status"]
    mjd = int(request.args["mjd"])

    success = await wrapBlocking(modifyDesignStatus, design_id, status, mjd)
    if success:
        return jsonify(status)
    else:
        return jsonify("failed")

@dbEndPoints.route('/lastEpoch/', methods=["GET"])
async def lastEpoch():
    pk = await wrapBlocking(latestFieldID)
    kwargs = getField(pk)
    epochs, last_design = designsToEpoch(**kwargs)

    last_status = await wrapBlocking(getDesignStatus, last_design)

    last_epoch = epochs[-1]

    last_epoch["field_id"] = kwargs.get("id")
    last_epoch["done"] = last_status == "done"
    last_epoch["field_pk"] = pk

    return jsonify(last_epoch)
