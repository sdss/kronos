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

    def __init__(self, design, scheduler=None):
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
        self.obsTimes = dict()
        self.haRange = [-60, 60]
        self.RS = scheduler

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
        self.obsTimes = dict()
        # in MJD, needed for rescheduling
        self.startTime = None
        self.haRange = [-60, 60]
        self.RS = scheduler  # keep track. bad form?
        self.designs = list()
        # self.backups = list()

    def schedule(self, mjd, duration=None):
        if duration is None:
            duration = design_time * len(self.designs)
        self.startTime = mjd
        startTime = Time(mjd, format="mjd").datetime
        self.obsTimes = {"start": startTime,
                         "end": startTime + datetime.timedelta(seconds=int(duration*86400))}
        now = startTime
        for d in self.designs:
            d.obsTimes["start"] = now
            now += datetime.timedelta(seconds=int(design_time*86400))
            d.obsTimes["end"] = now
        return mjd + duration
        # print(mjd, duration)
        # print(self.obsTimes["start"], "\n", self.obsTimes["end"])

    @property
    def haNow(self):
        now = Time.now()
        now.format = "mjd"
        lst = self.RS.lst(now.value)
        return float(self.RS.ralst2ha(ra=self.ra, lst=lst))

    # @property
    # def backups(self):
    #     if self._backups is None:
    #         self._backups = list()
    #         for i in range(1, 3):
    #             self._backups.append(field(9999, self.ra + i*30, self.dec + i*30, scheduler=self.RS))
    #             self._backups[-1].obsTimes = self.obsTimes
    #     return self._backups


class Queue(object):
    """wrapper around opsdb.Queue
    """

    def __init__(self):
        self.scheduler = Scheduler()
        self.queue = opsdb.Queue
        self.dbDesigns = self.queue.select()\
                                   .where(opsdb.Queue.position > 0)\
                                   .order_by(opsdb.Queue.position)
        self.designs = [Design(d.design.pk, self.scheduler.scheduler) for d in self.dbDesigns]
        self.fields = list()

        for d in self.designs:
            if d.fieldID not in [f.fieldID for f in self.fields]:
                self.fields.append(Field(d.field,
                                         scheduler=self.scheduler.scheduler))
                self.fields[-1].designs.append(d)
            else:
                w = np.where(d.fieldID == np.array([f.fieldID for f in self.fields]))
                self.fields[int(w[0])].designs.append(d)

    def scheduleFields(self, mjd_start, mjd_end):
        """fields are in order because designs are in order
           so run the night and fill it up
        """
        now = mjd_start
        for i, f in enumerate(self.fields):
            next_start = f.schedule(now)
            if next_start > mjd_end:
                # out of time, exclude remainder of fields
                self.fields = self.fields[:i + 1]
                break
            else:
                now = next_start


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
        field_ids, n_designs = self.scheduler.nextfield(mjd=mjd,
                                                        maxExp=exp,
                                                        live=True,
                                                        returnAll=True)

        fields = list()
        design_count = list()
        coords = list()
        for f, d in zip(field_ids, n_designs):
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
                design_count.append(d)
                coords.append([ra, dec])

        return fields, design_count, coords

    def scheduleMjd(self, mjd, redo=True):
        mjd_evening_twilight = self.scheduler.evening_twilight(mjd)
        mjd_morning_twilight = self.scheduler.morning_twilight(mjd)
        if not redo:
            return mjd_evening_twilight, mjd_morning_twilight
        opsdb.Queue.flushQueue()

        now = mjd_evening_twilight

        Field = targetdb.Field
        Design = targetdb.Design
        Version = targetdb.Version
        dbVersion = Version.get(plan=self.plan)

        while now < mjd_morning_twilight:
            exp_max = (mjd_morning_twilight - now) // self.exp_nom
            # field id and exposure nums of designs
            field_id, designs = self.scheduler.nextfield(mjd=now,
                                                         maxExp=exp_max,
                                                         live=True)
            designs = Design.select().join(Field)\
                            .where(Field.field_id == field_id,
                                   Field.version == dbVersion,
                                   Design.exposure << designs)
            for d in designs:
                # designs are i
                opsdb.Queue.appendQueue(d)

            now += len(designs) * self.exp_nom

        # test_fields = targetdb.Field.select().where(targetdb.Field.deccen > -30)
        # if len(test_fields) > 10:
        #     test_fields = test_fields[:10]

        # for f in test_fields:
        #     designs = targetdb.Design.select().where(targetdb.Design.field == f)
        #     for d in designs:
        #         opsdb.Queue.appendQueue(d)

        return mjd_evening_twilight, mjd_morning_twilight

# singleton may not be necessary, but it is probably helpful
# class Scheduler(object, metaclass=SchedulerSingleton):
#     """Wrap roboscheduler for useful interactive behavior
#     """

#     def __init__(self, observatory="apo", base=None):

#         # Set up schedule
#         self.scheduler = roboscheduler.scheduler.Scheduler(observatory=observatory)

#         # Initialize observedb
#         self.scheduler.initdb(designbase=base)
#         self.fields = self.scheduler.fields

#         self.duration = np.float32(18. / 60. / 24.)

#     def scheduleMjd(self, mjd):
#         mjd_evening_twilight = self.scheduler.evening_twilight(mjd)
#         mjd_morning_twilight = self.scheduler.morning_twilight(mjd)
#         curr_mjd = mjd_evening_twilight

#         fields = list()

#         while curr_mjd < mjd_morning_twilight:
#             maxExp = int((mjd_morning_twilight - curr_mjd)//self.duration)
#             fieldids, nexposures, priority, nexp_next = self.scheduler.nextfield(mjd=curr_mjd,
#                                                       maxExp=maxExp, returnAll=True)
#             if fieldids is not None:
#                 ipick = np.argmax(priority)
#                 fieldid = fieldids[ipick]
#                 pick_exp = nexposures[ipick]
#                 # fields.append(field(fieldid, self.fields.racen[fieldid],
#                 #                     self.fields.deccen[fieldid],
#                 #                     self.scheduler))
#                 # fields[-1].schedule(curr_mjd, pick_exp*self.duration)
#                 # fields[-1].addBackup(fieldid+1000, self.fields.racen[fieldid]+30,
#                 #                      self.fields.deccen[fieldid]+30)
#                 # for b in fields[-1].backups:
#                 #     b.schedule(curr_mjd, pick_exp*self.duration)
#                 curr_mjd = curr_mjd + pick_exp*self.duration

#             else:
#                 print(curr_mjd)
#                 curr_mjd = curr_mjd + self.duration

#         startTime = Time(mjd_evening_twilight, format="mjd").datetime
#         endTime = Time(mjd_morning_twilight, format="mjd").datetime

#         return fields, startTime, endTime


def chooseBackups(fieldids, priority, ras, decs, raMain, decMain):
    """takes priorities and coordinates of fields
       sorts into top picks away from "Main"
       returns a list of fieldids chosen
    """
    raCuts = [-60, -30, 0, 30, 60]
    return
