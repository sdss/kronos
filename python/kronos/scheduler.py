import datetime
import numpy as np
from astropy.time import Time

import roboscheduler.scheduler


# Class to define a singleton
class schedulerSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(schedulerSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class field(object):

    def __init__(self, fieldid, ra, dec, scheduler=None):
        self.fieldID = int(fieldid)
        self.ra = ra
        self.dec = dec
        self.obsTimes = None
        self.haRange = [-60, 60]
        self.RS = scheduler  # keep track. bad form?
        self.backups = list()

    def schedule(self, mjd, duration):
        startTime = Time(mjd, format="mjd").datetime
        self.obsTimes = {"start": startTime,
                         "end": startTime + datetime.timedelta(seconds=int(duration*86400))}
        # print(mjd, duration)
        # print(self.obsTimes["start"], "\n", self.obsTimes["end"])

    def addBackup(self, fieldid, ra, dec):
        self.backups.append(field(fieldid, ra, dec, scheduler=self.RS))

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


# singleton may not be necessary, but it is probably helpful
class Scheduler(object, metaclass=schedulerSingleton):
    """Wrap roboscheduler for useful interactive behavior
    """

    def __init__(self, observatory="apo", base=None):

        # Set up schedule
        self.scheduler = roboscheduler.scheduler.Scheduler(observatory=observatory)

        # Initialize observedb
        self.scheduler.initdb(designbase=base)
        self.fields = self.scheduler.fields

        self.duration = np.float32(18. / 60. / 24.)

    def scheduleMjd(self, mjd):
        mjd_evening_twilight = self.scheduler.evening_twilight(mjd)
        mjd_morning_twilight = self.scheduler.morning_twilight(mjd)
        curr_mjd = mjd_evening_twilight

        fields = list()

        while curr_mjd < mjd_morning_twilight:
            maxExp = int((mjd_morning_twilight - curr_mjd)//self.duration)
            fieldids, nexposures, priority = self.scheduler.nextfield(mjd=curr_mjd,
                                                      maxExp=maxExp, returnAll=True)
            if fieldids is not None:
                ipick = np.argmax(priority)
                fieldid = fieldids[ipick]
                pick_exp = nexposures[ipick]
                fields.append(field(fieldid, self.fields.racen[fieldid],
                                    self.fields.deccen[fieldid],
                                    self.scheduler))
                fields[-1].schedule(curr_mjd, pick_exp*self.duration)
                fields[-1].addBackup(fieldid+1000, self.fields.racen[fieldid]+30,
                                     self.fields.deccen[fieldid]+30)
                for b in fields[-1].backups:
                    b.schedule(curr_mjd, pick_exp*self.duration)
                curr_mjd = curr_mjd + pick_exp*self.duration

            else:
                print(curr_mjd)
                curr_mjd = curr_mjd + self.duration

        startTime = Time(mjd_evening_twilight, format="mjd").datetime
        endTime = Time(mjd_morning_twilight, format="mjd").datetime

        return fields, startTime, endTime


def chooseBackups(fieldids, priority, ras, decs, raMain, decMain):
    """takes priorities and coordinates of fields
       sorts into top picks away from "Main"
       returns a list of fieldids chosen
    """
    raCuts = [-60, -30, 0, 30, 60]
    return
