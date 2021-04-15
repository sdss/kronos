from collections import defaultdict

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb, targetdb

from kronos import rs_version


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


def fieldQuery(cadence=None, priority=None, limit=100):
    """query targetdb for fields matching parameters
    """

    dbCad = targetdb.Cadence
    if cadence is not None:
        matchingCad = dbCad.select().where(dbCad.label.contains(cadence))
    else:
        matchingCad = dbCad.select()

    dbField = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)

    if priority is not None:
        fp = opsdb.FieldPriority
        f2p = opsdb.FieldToPriority
        priority = fp.get(label=priority)
        fields = dbField.select().join(f2p, on=(f2p.field_pk == dbField.pk))\
                                 .join(fp, on=(fp.pk == f2p.field_priority_pk))\
                                 .where(fp.pk == priority.pk,
                                        dbField.cadence << matchingCad,
                                        dbField.version == dbVersion)\
                                 .limit(limit)
    else:
        fields = dbField.select().where(dbField.cadence << matchingCad,
                                        dbField.version == dbVersion)\
                                 .limit(limit)

    # select returns query object, we want a list
    return [f for f in fields]


def getCadences():
    cadQuery = targetdb.Cadence.select()
    # select returns query object, we want a list
    return [c for c in cadQuery]
