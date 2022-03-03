from collections import defaultdict
from operator import itemgetter

from astropy.time import Time
from peewee import fn

from sdssdb.peewee.sdss5db import opsdb, targetdb

from kronos import rs_version, observatory  # , wrapBlocking
from kronos.scheduler import design_time


def getRecentExps(mjd):
    r1_db = opsdb.Camera.get(label="r1")
    b1_db = opsdb.Camera.get(label="b1")
    ap_db = opsdb.Camera.get(label="APOGEE")
    db_flavor = opsdb.ExposureFlavor.get(pk=1)  # science

    useTime = Time(mjd - 1, format="mjd").datetime

    cf = opsdb.CameraFrame
    exp = opsdb.Exposure
    cfg = opsdb.Configuration

    exps = cf.select(exp.pk, cf.sn2, cf.camera_pk, exp.start_time,
                     exp.exposure_no, cfg.design_id)\
                .join(exp)\
                .join(cfg)\
                .where(exp.start_time > useTime,
                       exp.exposure_flavor == db_flavor).dicts()

    exp_dicts = {e["pk"]: {"pk": e["pk"], "r1": "--", "b1": "--", "AP": "--"} for e in exps}
    exp_list = list()

    for e in exps:
        # exp_dict = {"pk": int(e.pk),
        #             "design": 0,
        #             "timeStamp": "",
        #             "r1": "--",
        #             "b1": "--",
        #             "AP": "--"}
        exp_dicts[e["pk"]]["design"] = int(e["design"])
        exp_dicts[e["pk"]]["exposure_no"] = int(e["exposure_no"])
        exp_dicts[e["pk"]]["timeStamp"] = e["start_time"].strftime("%H:%M:%S")
        # for f in e.CameraFrames:
        if e["camera"] == r1_db.pk and e["sn2"] is not None:
            exp_dicts[e["pk"]]["r1"] = f"{e['sn2']:.2f}"
        if e["camera"] == b1_db.pk and e["sn2"] is not None:
            exp_dicts[e["pk"]]["b1"] = f"{e['sn2']:.2f}"
        if e["camera"] == ap_db.pk and e["sn2"] is not None:
            exp_dicts[e["pk"]]["AP"] = f"{e['sn2']:.1f}"
    for e in exp_dicts:
        exp_list.append(exp_dicts[e])

    exp_list = sorted(exp_list, key=itemgetter('pk'), reverse=True)

    return exp_list


def fieldQuery(cadence=None, priority=None, ra_range=None, limit=100):
    """query targetdb for fields matching parameters
    """

    dbCad = targetdb.Cadence
    if cadence is not None:
        matchingCad = dbCad.select().where(dbCad.label.contains(cadence))
    else:
        matchingCad = dbCad.select()

    dbField = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)

    obsDB = targetdb.Observatory()
    obs = obsDB.get(label=observatory)

    if priority is not None:
        fp = opsdb.FieldPriority
        f2p = opsdb.FieldToPriority
        priority = fp.get(label=priority)
        fields = dbField.select().join(f2p, on=(f2p.field_pk == dbField.pk))\
                                 .join(fp, on=(fp.pk == f2p.field_priority_pk))\
                                 .where(fp.pk == priority.pk,
                                        dbField.cadence << matchingCad,
                                        dbField.version == dbVersion,
                                        dbField.observatory == obs)\
                                 .limit(limit)
    else:
        fields = dbField.select().where(dbField.cadence << matchingCad,
                                        dbField.version == dbVersion,
                                        dbField.observatory == obs)\
                                 .limit(limit)

    if ra_range:
        assert len(ra_range) == 2, "must specify only begin and end of RA range"
        # print("RA RAGE", ra_range)
        if ra_range[0] > ra_range[1]:
            # implied between ra_range[1] and 360, or between 0 and ra_range[0]
            fields = fields.where((dbField.racen > ra_range[0]) |
                                  (dbField.racen < ra_range[1])).order_by(dbField.racen)
        else:
            fields = fields.where((dbField.racen > ra_range[0]) &
                                  (dbField.racen < ra_range[1])).order_by(dbField.racen)

    # print(fields.sql())
    # select returns query object, we want a list
    return [f for f in fields]


def getCadences():
    cadQuery = targetdb.Cadence.select()
    # select returns query object, we want a list
    return [c for c in cadQuery]


def prioritizeField(fieldPk):
    """set a field to top priority
    """
    dbPriority = opsdb.FieldPriority.get(label="top")
    f2p, created = opsdb.FieldToPriority.get_or_create(field_pk=fieldPk)
    f2p.FieldPriority = dbPriority
    f2p.save()


def disableField(fieldPk):
    """set a field to disabled
    """
    dbPriority = opsdb.FieldPriority.get(label="disabled")
    f2p, created = opsdb.FieldToPriority.get_or_create(field_pk=fieldPk)
    f2p.FieldPriority = dbPriority
    f2p.save()


def resetField(fieldPk):
    """remove any special status on a field
    """
    q = opsdb.FieldToPriority.delete().where(opsdb.FieldToPriority.field_pk == fieldPk)
    removed = q.execute()
    assert removed != 0, "Should not have been able to delete"


def getField(field_id):
    """grab a field from targetdb and touch some foreign keys while
       in the blocking call so that's taken care of
    """

    r1_db = opsdb.Camera.get(label="r1")
    b1_db = opsdb.Camera.get(label="b1")
    ap_db = opsdb.Camera.get(label="APOGEE")
    db_flavor = opsdb.ExposureFlavor.get(pk=1)
    dbField = targetdb.Field

    field = dbField.get(field_id=field_id)
    # designs = field.designs.select()

    exp_query = opsdb.Exposure.select()\
                     .join(opsdb.Configuration)\
                     .join(targetdb.Design,
                           on=(targetdb.Design.design_id == opsdb.Configuration.design_id))\
                     .join(dbField)\
                     .where(dbField.field_id == field_id,
                            opsdb.Exposure.exposure_flavor == db_flavor)

    exps = defaultdict(list)
    for e in exp_query:
        exp_dict = {"design": 0,
                    "timeStamp": "",
                    "r1": 0,
                    "b1": 0,
                    "AP": 0}
        exp_dict["design"] = int(e.configuration.design.design_id)
        exp_dict["timeStamp"] = e.start_time.strftime("%H:%M:%S")
        exp_mjd = int(Time(e.start_time).mjd)  # this truncates so it's probably "wrong", TBD
        for f in e.CameraFrames:
            if f.camera.pk == r1_db.pk and f.sn2 is not None and f.sn2 > 0.5:
                exp_dict["r1"] = f.sn2
            if f.camera.pk == b1_db.pk and f.sn2 is not None and f.sn2 > 0.5:
                exp_dict["b1"] = f.sn2
            if f.camera.pk == ap_db.pk and f.ql_sn2 is not None and f.ql_sn2 > 100:
                exp_dict["AP"] = f.ql_sn2
        exps[exp_mjd].append(exp_dict)

    sums = dict()
    exps_export = defaultdict(list)
    for d, eps in exps.items():
        sums[d] = dict()

        r1_sum = sum([e["r1"] for e in eps])
        if r1_sum > 0:
            sums[d]["r1"] = f"{r1_sum:.2f}"
        else:
            sums[d]["r1"] = "--"
        b1_sum = sum([e["b1"] for e in eps])
        if b1_sum > 0:
            sums[d]["b1"] = f"{b1_sum:.2f}"
        else:
            sums[d]["b1"] = "--"
        AP_sum = sum([e["AP"] for e in eps])
        if AP_sum > 0:
            sums[d]["AP"] = f"{AP_sum:.1f}"
        else:
            sums[d]["AP"] = "--"

        for edict in eps:
            # nonZero = False
            for k in ["r1", "b1", "AP"]:
                if edict[k] > 0:
                    # nonZero = True
                    edict[k] = f"{edict[k]:.1f}"
                else:
                    edict[k] = "--"
            # if nonZero:
            exps_export[d].append(edict)

    return {"id": field_id,
            "ra": field.racen,
            "dec": field.deccen,
            "observatory": field.observatory.label,
            "cadence": field.cadence.label,
            "exps": exps_export,
            "sums": sums}


def getConfigurations(design_id=None):
    r1_db = opsdb.Camera.get(label="r1")
    b1_db = opsdb.Camera.get(label="b1")
    ap_db = opsdb.Camera.get(label="APOGEE")
    db_flavor = opsdb.ExposureFlavor.get(pk=1)
    dbDesign = targetdb.Design

    exp_query = opsdb.Exposure.select()\
                     .join(opsdb.Configuration)\
                     .join(targetdb.Design,
                           on=(targetdb.Design.design_id == opsdb.Configuration.design_id))\
                     .where(dbDesign.design_id == design_id,
                            opsdb.Exposure.exposure_flavor == db_flavor)

    exps = defaultdict(list)
    for e in exp_query:
        exp_dict = {"timeStamp": "",
                    "r1": 0,
                    "b1": 0,
                    "AP": 0}
        conf_id = int(e.configuration.configuration_id)
        exp_dict["timeStamp"] = e.start_time.strftime("%Y-%m-%d")
        # exp_mjd = int(Time(e.start_time).mjd)  # this truncates so it's probably "wrong", TBD
        for f in e.CameraFrames:
            if f.camera.pk == r1_db.pk and f.sn2 is not None and f.sn2 > 0.2:
                exp_dict["r1"] = f.sn2
            if f.camera.pk == b1_db.pk and f.sn2 is not None and f.sn2 > 0.2:
                exp_dict["b1"] = f.sn2
            if f.camera.pk == ap_db.pk and f.ql_sn2 is not None and f.ql_sn2 > 100:
                exp_dict["AP"] = f.ql_sn2
        exps[conf_id].append(exp_dict)

    configurations = list()
    for c, eps in exps.items():
        conf = dict()
        conf["timeStamp"] = eps[-1]["timeStamp"]
        conf["id"] = c
        nonZero = False
        r1_sum = sum([e["r1"] for e in eps])
        if r1_sum > 0:
            nonZero = True
            conf["r1"] = f"{r1_sum:.2f}"
        else:
            conf["r1"] = "--"
        b1_sum = sum([e["b1"] for e in eps])
        if b1_sum > 0:
            nonZero = True
            conf["b1"] = f"{b1_sum:.2f}"
        else:
            conf["b1"] = "--"
        AP_sum = sum([e["AP"] for e in eps])
        if AP_sum > 0:
            nonZero = True
            conf["AP"] = f"{AP_sum:.1f}"
        else:
            conf["AP"] = "--"
        if nonZero:
            configurations.append(conf)

    return configurations


def designQuery(field_id=None, ra_range=None, dbStatus=None, carton=None,
                limit=100, pa_range=None, instrument="BOSS", orderby=None,
                design_ids=[]):

    compStatus = opsdb.CompletionStatus
    d2s = opsdb.DesignToStatus

    dbDesign = targetdb.Design
    dbField = targetdb.Field
    Assign = targetdb.Assignment
    Inst = targetdb.Instrument

    obsDB = targetdb.Observatory()
    obs = obsDB.get(label=observatory)

    qInst = Inst.get(label=instrument)

    designs = dbDesign.select(compStatus.label, dbDesign.design_id, dbField.field_id,
                              dbField.racen, dbField.deccen, dbField.position_angle,
                              fn.COUNT(Assign.pk))\
                      .join(d2s, on=(d2s.design_id == dbDesign.design_id))\
                      .join(compStatus, on=(d2s.completion_status_pk == compStatus.pk))\
                      .switch(dbDesign)\
                      .join(dbField, on=(dbField.pk == dbDesign.field_pk))\
                      .switch(dbDesign)\
                      .join(Assign, on=(dbDesign.design_id == Assign.design_id))\
                      .where(dbField.observatory == obs, Assign.instrument_pk == qInst.pk)\
                      .limit(limit)

    designs = designs.group_by(compStatus.label, dbDesign.design_id,
                               dbField.field_id, dbField.racen,
                               dbField.deccen, dbField.position_angle)



    if field_id is not None:
        designs = designs.where(dbField.field_id == field_id)

    if dbStatus is not None:
        designs = designs.where(compStatus.label == dbStatus)

    if carton is not None:
        C2T = targetdb.CartonToTarget
        Carton = targetdb.Carton
        matchingCartons = Carton.select().where(Carton.carton.contains(carton))
        designs = designs.join(C2T, on=(Assign.carton_to_target_pk == C2T.pk))\
                         .where(C2T.carton << matchingCartons)


    if ra_range and field_id is None:
        assert len(ra_range) == 2, "must specify only begin and end of RA range"
        if ra_range[0] > ra_range[1]:
            # implied between ra_range[1] and 360, or between 0 and ra_range[0]
            designs = designs.where((dbField.racen > ra_range[0]) |
                                    (dbField.racen < ra_range[1]))
        else:
            designs = designs.where((dbField.racen > ra_range[0]) &
                                    (dbField.racen < ra_range[1]))

    if pa_range and field_id is None:
        assert len(pa_range) == 2, "must specify only begin and end of position angle range"
        designs = designs.where((dbField.position_angle >= pa_range[0]) &
                                (dbField.position_angle <= pa_range[1]))

    if orderby is not None:
        translate = {"designID": dbDesign.design_id,
                     "fieldID": dbField.field_id,
                     "RA": dbField.racen,
                     "PA": dbField.position_angle}
        designs = designs.order_by(translate[orderby])

    if len(design_ids) > 0:
        designs = designs.where(dbDesign.design_id << design_ids)

    resTuples = designs.tuples()

    designIDS = [r[1] for r in resTuples]
    if instrument == "BOSS":
        qInst = Inst.get(label="APOGEE")
    else:
        qInst = Inst.get(label="BOSS")

    ocounts = dbDesign.select(fn.COUNT(Assign.pk), dbDesign.design_id)\
                      .join(Assign, on=(dbDesign.design_id == Assign.design_id))\
                      .group_by(dbDesign.design_id)\
                      .where(Assign.instrument_pk == qInst.pk,
                             dbDesign.design_id << designIDS)

    dCounts = {c[1]: c[0] for c in ocounts.tuples()}

    res = [{"label": d[0],
            "design_id": d[1],
            "field_id": d[2],
            "racen": d[3],
            "deccen": d[4],
            "position_angle": d[5],
            "assigned": d[6],
            "oassigned": dCounts.get(d[1], 0)} for d in resTuples]

    return res


def designDetails(design):
    if isinstance(design, targetdb.Design):
        design = design.design_id

    Design = targetdb.Design
    Carton = targetdb.Carton
    c2t = targetdb.CartonToTarget
    Assignment = targetdb.Assignment

    cartons = Carton.select(Carton.carton)\
                    .join(c2t, on=(Carton.pk == c2t.carton_pk))\
                    .join(Assignment, on=(Assignment.carton_to_target == c2t.pk))\
                    .join(Design, on=(Assignment.design_id == Design.design_id))\
                    .where(Design.design_id == design)

    CompStatus = opsdb.CompletionStatus
    d2s = opsdb.DesignToStatus

    status = CompStatus.select(CompStatus.label)\
                       .join(d2s, on=(d2s.completion_status_pk == CompStatus.pk))\
                       .where(d2s.design_id == design)

    status = status[0].label

    cartons = [c.carton for c in cartons]

    return status, cartons


def cartonLabels():
    Carton = targetdb.Carton

    cartons = Carton.select(Carton.carton)

    return [c.carton for c in cartons]


def safeInsertInQueue(design_id, pos, mjd_plan=None):
    Queue = opsdb.Queue

    count = Queue.select().count()

    if pos >= count:
        # queue starts at 1 not 0
        pos = count
    if pos <= 0:
        pos = 1

    opsdb.Queue.insertInQueue(design_id, pos, mjd=mjd_plan)


def safeAppendQueue(design_id, mjd_plan=None):
    """Basically all this does is allow appending to an empty queue
       with mjd = "now" (or w/e is passed), otherwise it increments
       the queue mjd.
    """
    Queue = opsdb.Queue

    mjds = [m.mjd_plan for m in Queue.select(Queue.mjd_plan).order_by(Queue.position)]

    if len(mjds) > 0:
        if mjds[-1] is not None:
            mjd_plan = mjds[-1] + design_time

    Queue.appendQueue(design_id, mjd_plan=mjd_plan)


def designCompletion(designs):
    assert type(designs) == list, "expecting list of design_ids"
    Design = targetdb.Design

    CompStatus = opsdb.CompletionStatus
    d2s = opsdb.DesignToStatus

    status = CompStatus.select(CompStatus.label, Design.design_id)\
                       .join(d2s, on=(d2s.completion_status_pk == CompStatus.pk))\
                       .join(Design, on=(d2s.design_id == Design.design_id))\
                       .where(Design.design_id << designs)

    return [{"design_id": s[1], "status": s[0]} for s in status.tuples()]


def queueLength():
    Queue = opsdb.Queue
    return Queue.select(fn.COUNT(Queue.pk)).where(Queue.position > 0).scalar()


def apql():
    exp = opsdb.Exposure
    ql = opsdb.Quicklook
    Design = targetdb.Design
    conf = opsdb.Configuration

    latest = exp.select(fn.MAX(exp.pk)).join(ql).scalar()

    design = Design.select(Design.design_id)\
                   .join(conf).join(exp)\
                   .where(exp.pk == latest).scalar()

    reads = ql.select(ql.readnum, ql.snr_standard_scale).where(ql.exposure_pk == latest).tuples()

    out = {"design": design, "reads": [[r[0], r[1]] for r in reads]}

    return out
