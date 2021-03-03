import datetime
import numpy as np
from astropy.time import Time

import roboscheduler.scheduler
from sdssdb.peewee.sdss5db import opsdb, targetdb

if not opsdb.database.connected:
    opsdb.database.connect_from_parameters(user='sdss_user',
                                           host='localhost',
                                           port=5432)

design_time = 18. / 60. / 24.  # days, keep in mjd


# Class to define a singleton
class SchedulerSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SchedulerSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Design(object):
    """wrap db design
    """

    def __init__(self, design, scheduler=None, mjd_plan=None):
        if isinstance(design, targetdb.Design):
            self.designID = int(design.pk)
            self.dbDesign = design
        else:
            self.designID = int(design)
            self.dbDesign = targetdb.Design.get(pk=self.designID)
        self.field = self.dbDesign.field
        self.fieldID = self.field.field_id
        self.ra = self.field.racen
        self.dec = self.field.deccen
        # self.obsTimes = dict()
        self.haRange = [-60, 60]
        self.RS = scheduler
        self.mjd_plan = mjd_plan

    @property
    def haNow(self):
        now = Time.now()
        now.format = "mjd"
        lst = self.RS.lst(now.value)
        return float(self.RS.ralst2ha(ra=self.ra, lst=lst))


class Field(object):
    """wrap db field. this is what we show on sky
       and in viz windows
    """

    def __init__(self, field, scheduler=None):
        if isinstance(field, targetdb.Field):
            self.fieldID = int(field.field_id)
            self.dbField = field
        else:
            self.fieldID = int(field)
            self.dbField = targetdb.Field.get(field_id=self.field_id)
        self.ra = self.dbField.racen
        self.dec = self.dbField.deccen
        self._obsTimes = None
        self._startTime = None
        # in MJD, needed for rescheduling
        self.haRange = [-60, 60]
        self.RS = scheduler  # keep track. bad form?
        self.designs = list()
        # self.backups = list()

    def _timesFromDesigns(self):
        """startTime and obsTimes need to get info from designs
        """
        start = np.max([d.mjd_plan for d in self.designs])
        self._startTime = start
        startTime = Time(start, format="mjd").datetime,
        if type(startTime) is tuple:
            startTime = startTime[0]
        mjd_duration = len(self.designs) * design_time
        endTime = startTime + datetime.timedelta(seconds=int(mjd_duration*86400))
        self._obsTimes = {"start": startTime,
                          "end": endTime}

    @property
    def obsTimes(self):
        if self._obsTimes is None:
            self._timesFromDesigns()
        return self._obsTimes

    @property
    def startTime(self):
        if self._startTime is None:
            self._timesFromDesigns()
        return self._startTime

    @property
    def haNow(self):
        now = Time.now()
        now.format = "mjd"
        lst = self.RS.lst(now.value)
        return float(self.RS.ralst2ha(ra=self.ra, lst=lst))


class Queue(object):
    """wrapper around opsdb.Queue
    """

    def __init__(self):
        self.scheduler = Scheduler()
        self.queue = opsdb.Queue
        self.dbDesigns = self.queue.select()\
                                   .where(opsdb.Queue.position > 0)\
                                   .order_by(opsdb.Queue.position)
        self.designs = [Design(d.design.pk,
                               scheduler=self.scheduler.scheduler,
                               mjd_plan=d.mjd_plan)
                        for d in self.dbDesigns]
        self.fields = list()

        for d in self.designs:
            if d.fieldID not in [f.fieldID for f in self.fields]:
                self.fields.append(Field(d.field,
                                         scheduler=self.scheduler.scheduler))
                self.fields[-1].designs.append(d)
            else:
                w = np.where(d.fieldID == np.array([f.fieldID for f in self.fields]))
                self.fields[int(w[0])].designs.append(d)


# singleton may not be necessary, but it is probably helpful
class Scheduler(object, metaclass=SchedulerSingleton):
    """dummy schedule for queue testing without full DB
    """

    def __init__(self, **kwargs):
        self.plan = "test-newfield-hack"
        self.scheduler = roboscheduler.scheduler.Scheduler(observatory="apo")
        self.scheduler.initdb(designbase=self.plan, fromFits=False)
        self.exp_nom = 18 / 60 / 24

    def choiceFields(self, mjd, exp=8):
        """return multiple fields for user to choose from
           at a specific mjd
        """
        field_ids = self.scheduler.nextfield(mjd=mjd,
                                             maxExp=exp,
                                             live=True,
                                             returnAll=True)

        fields = list()
        # design_count = list()
        coords = list()
        for f in field_ids:
            if len(fields) > 3:
                continue
            idx = np.where(self.scheduler.fields.field_id == f)
            ra = self.scheduler.fields.racen[idx]
            dec = self.scheduler.fields.deccen[idx]
            far_enough = True
            for c in coords:
                d = ((c[0] - ra)*np.cos(dec*np.pi/180))**2 + (dec - c[1])**2
                if d < 45**2:
                    far_enough = False
                    break
            if far_enough:
                fields.append(f)
                # design_count.append(d)
                coords.append([ra, dec])

        return fields, coords

    def replaceField(self, oldField, backup):
        """replace oldField with backup
        """
        newDesigns = self.scheduler.designsNext(backup)

        oldPositions = opsdb.Queue.rm(oldField, returnPositions=True)

        Field = targetdb.Field
        Design = targetdb.Design
        Version = targetdb.Version
        dbVersion = Version.get(plan=self.plan)
        designs = Design.select().join(Field)\
                                 .where(Field.field_id == backup,
                                        Field.version == dbVersion,
                                        Design.exposure << newDesigns)

        queuePos = min(oldPositions)
        for d in designs:
            # designs are i
            opsdb.Queue.insertInQueue(d, queuePos)
            queuePos += 1

    def queueFromSched(self, mjdStart, mjdEnd, redo=True):
        now = mjdStart

        Field = targetdb.Field
        Design = targetdb.Design
        Version = targetdb.Version
        dbVersion = Version.get(plan=self.plan)

        while now < mjdEnd:
            exp_max = (mjdEnd - now) // self.exp_nom
            # field id and exposure nums of designs
            field_id, designs = self.scheduler.nextfield(mjd=now,
                                                         maxExp=exp_max,
                                                         live=True)
            designs = Design.select().join(Field)\
                            .where(Field.field_id == field_id,
                                   Field.version == dbVersion,
                                   Design.exposure << designs)
            for i, d in enumerate(designs):
                mjd_plan = now + i*self.exp_nom
                opsdb.Queue.appendQueue(d, mjd_plan)

            now += len(designs) * self.exp_nom

    def scheduleMjd(self, mjd, redo=True):
        mjd_evening_twilight = self.scheduler.evening_twilight(mjd)
        mjd_morning_twilight = self.scheduler.morning_twilight(mjd)
        if not redo:
            return mjd_evening_twilight, mjd_morning_twilight
        opsdb.Queue.flushQueue()

        self.queueFromSched(mjd_evening_twilight, mjd_morning_twilight,
                            redo=True)

        return mjd_evening_twilight, mjd_morning_twilight

    def rescheduleAfterField(self, mjd, fieldID):
        queue = Queue()

        field = queue.fields[[f.fieldID for f in queue.fields] == replace]
        args = scheduler.choiceFields(field.startTime)

        oldPositions = opsdb.Queue.rm(oldField, returnPositions=True)

        Field = targetdb.Field
        Design = targetdb.Design
        Version = targetdb.Version
        dbVersion = Version.get(plan=self.plan)
        designs = Design.select().join(Field)\
                                 .where(Field.field_id == backup,
                                        Field.version == dbVersion,
                                        Design.exposure << newDesigns)

        queuePos = min(oldPositions)
