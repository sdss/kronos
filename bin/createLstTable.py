import os

import numpy as np

import sdssdb.peewee.sdss5db.opsdb as opsdb
import sdssdb.peewee.sdss5db.targetdb as targetdb
from roboscheduler import scheduler

observatory = os.environ["OBSERVATORY"]
plan = os.environ["RS_VERSION"]
scheduler = scheduler.Scheduler(observatory=observatory.lower())

versionDB = targetdb.Version()
ver = versionDB.get(plan=plan)

obsDB = targetdb.Observatory()
obs = obsDB.get(label=observatory.upper())

Field = targetdb.Field
Design = targetdb.Design
d2f = targetdb.DesignToField
Status = opsdb.CompletionStatus
d2s = opsdb.DesignToStatus
LstHist = opsdb.LstHist
done = Status.get(label="done")

dbfields = Field.select(d2s.mjd, Field.pk)\
                .join(d2f, on=(Field.pk == d2f.field_pk))\
                .join(Design, on=(Design.design_id == d2f.design_id))\
                .join(d2s, on=(Design.design_id == d2s.design_id))\
                .where((Field.version == ver) &
                        (Field.observatory == obs),
                        (d2s.status == done)).dicts()

allfields = Field.select(Field.pk).where(Field.version == ver, Field.observatory == obs).dicts()

hist = {f["pk"]: list() for f in allfields}

for d in dbfields:
    hist[d["pk"]].append(d["mjd"])

lstObs = np.zeros((len(hist), 24, 2), dtype=np.int32)

for i, pk in enumerate(hist.keys()):
    skybrightness = [float(scheduler.skybrightness(m)) for m in hist[pk]]
    dark = np.array(skybrightness) <= 0.35
    lst = np.round(scheduler.lst(hist[pk])/15, 0).astype(int)
    if 24 in lst:
        lst = [i if i != 24 else 0 for i in lst]
        lst = np.array(lst)
    dark_lsts = lst[np.where(dark)]
    unique, counts = np.unique(dark_lsts, return_counts=True)
    for l, c in zip(unique, counts):
        lstObs[i][l, 0] += c
    bright_lsts = lst[np.where(~dark)]
    unique, counts = np.unique(bright_lsts, return_counts=True)
    for l, c in zip(unique, counts):
        lstObs[i][l, 1] += c

for k, pk in enumerate(hist.keys()):
    lst = [[int(i), int(j)] for i, j in lstObs[k]]
    print(lst)
    entry = LstHist.create(field_pk=pk, lst_counts=lst)
    print(entry)
    entry.save()
