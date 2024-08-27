#!/usr/bin/env/python

from datetime import datetime

from quart import Blueprint, request, jsonify

import numpy as np

from kronos import wrapBlocking
from kronos.dbConvenience import (getRecentExps, designCompletion,
                                  queueLength, getDesignStatus,
                                  apql, modifyDesignStatus,
                                  getField, latestFieldID,
                                  predictNext)
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
    kwargs = await wrapBlocking(getField, pk)
    epochs, last_design = designsToEpoch(**kwargs)

    if last_design:
        last_status = await wrapBlocking(getDesignStatus, last_design)
    else:
        last_status = "not done"

    last_epoch = epochs[-1]

    last_epoch["field_id"] = kwargs.get("id")
    last_epoch["done"] = last_status == "done"
    last_epoch["field_pk"] = pk

    return jsonify(last_epoch)


@dbEndPoints.route('/status/', methods=['GET'])
async def status():
    res = await wrapBlocking(predictNext)

    return jsonify(res)


@dbEndPoints.route('/predBoss/', methods=['GET'])
async def predBoss():
    predictions = np.genfromtxt("/home/jdonor/pred_snr.test", 
                  dtype=None, delimiter="|", names=True,
                  encoding="UTF-8")
    
    b_pk = 2
    r_pk = 1

    b_mask = np.where(predictions["camera_pk"] == b_pk)[0][:1000]
    r_mask = np.where(predictions["camera_pk"] == r_pk)[0][:1000]
    r_time_array = predictions["gfa_date_obs"][b_mask]
    b_time_array = predictions["gfa_date_obs"][b_mask]
    format = '%Y-%m-%d %H:%M:%S.%f'
    b_times = [datetime.strptime(d.strip(), format) for d in b_time_array]
    r_times = [datetime.strptime(d.strip(), format) for d in r_time_array]
    outformat = "%Y-%m-%d %H:%M:%S"
    output = {
        "b_sn" : list(predictions["pred_value"][b_mask]),
        "r_sn" : list(predictions["pred_value"][r_mask]),
        "b_times" : [d.strftime(outformat) for d in b_times],
        "r_times" : [d.strftime(outformat) for d in r_times],
    }

    return jsonify(output)
