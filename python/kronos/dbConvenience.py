from collections import defaultdict

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb, targetdb

from kronos import rs_version, observatory  # , wrapBlocking


def getRecentExps(mjd):
    r1_db = opsdb.Camera.get(label="r1")
    b1_db = opsdb.Camera.get(label="b1")
    ap_db = opsdb.Camera.get(label="APOGEE")
    db_flavor = opsdb.ExposureFlavor.get(pk=1)  # science

    useTime = Time(mjd - 1, format="mjd").datetime

    exps = opsdb.Exposure.select()\
                .join(opsdb.Configuration)\
                .join(targetdb.Design,
                      on=(targetdb.Design.pk == opsdb.Configuration.design_pk))\
                .where(opsdb.Exposure.start_time > useTime,
                       opsdb.Exposure.exposure_flavor == db_flavor)

    exp_list = list()

    for e in exps:
        exp_dict = {"design": 0,
                    "timeStamp": "",
                    "r1": "--",
                    "b1": "--",
                    "AP": "--"}
        exp_dict["design"] = int(e.configuration.design.pk)
        exp_dict["timeStamp"] = e.start_time.strftime("%H:%M:%S")
        for f in e.CameraFrames:
            if f.camera == r1_db:
                exp_dict["r1"] = f.ql_sn2
            if f.camera == b1_db:
                exp_dict["b1"] = f.ql_sn2
            if f.camera == ap_db:
                exp_dict["AP"] = f.ql_sn2
        exp_list.append(exp_dict)

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


def getField(fieldId):
    """grab a field from targetdb and touch some foreign keys while
       in the blocking call so that's taken care of
    """

    r1_db = opsdb.Camera.get(label="r1")
    b1_db = opsdb.Camera.get(label="b1")
    ap_db = opsdb.Camera.get(label="APOGEE")
    db_flavor = opsdb.ExposureFlavor.get(pk=1)
    dbField = targetdb.Field

    field = dbField.get(field_id=fieldId)
    designs = field.designs.select()

    exp_query = opsdb.Exposure.select()\
                     .join(opsdb.Configuration)\
                     .join(targetdb.Design,
                           on=(targetdb.Design.pk == opsdb.Configuration.design_pk))\
                     .join(dbField)\
                     .where(dbField.field_id == fieldId,
                            opsdb.Exposure.exposure_flavor == db_flavor)

    exps = defaultdict(list)
    for e in exp_query:
        exp_dict = {"design": 0,
                    "timeStamp": "",
                    "r1": 0,
                    "b1": 0,
                    "AP": 0}
        exp_dict["design"] = int(e.configuration.design.pk)
        exp_dict["timeStamp"] = e.start_time.strftime("%H:%M:%S")
        exp_mjd = int(Time(e.start_time).mjd)  # this truncates so it's probably "wrong", TBD
        for f in e.CameraFrames:
            if f.camera == r1_db:
                exp_dict["r1"] = f.ql_sn2
            if f.camera == b1_db:
                exp_dict["b1"] = f.ql_sn2
            if f.camera == ap_db:
                exp_dict["AP"] = f.ql_sn2
        exps[exp_mjd].append(exp_dict)

    sums = dict()
    for d, eps in exps.items():
        sums[d] = dict()
        sums[d]["r1"] = sum([e["r1"] for e in eps])
        sums[d]["b1"] = sum([e["b1"] for e in eps])
        sums[d]["AP"] = sum([e["AP"] for e in eps])
        # sums[d]["r1"] = sum([e["r1"] if e["r1"] else 0 for e in eps])
        # sums[d]["b1"] = sum([e["b1"] if e["b1"] else 0 for e in eps])
        # sums[d]["AP"] = sum([e["AP"] if e["AP"] else 0 for e in eps])

    return {"id": fieldId,
            "ra": field.racen,
            "dec": field.deccen,
            "observatory": field.observatory.label,
            "cadence": field.cadence.label,
            "exps": exps,
            "sums": sums}
