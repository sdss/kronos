import asyncio
import datetime
import numpy as np
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import SkyCoord

import roboscheduler.scheduler
from sdssdb.peewee.sdss5db import opsdb, targetdb

from kronos import rs_version, wrapBlocking, observatory
from kronos.site import Site

if not opsdb.database.connected:
    print("!! CONFIG !!", opsdb.database._config)

design_time = 18. / 60. / 24.  # days, keep in mjd


def offsetNow():
    now = Time.now()
    now.format = "mjd"
    mjd_now = now.value
    # use an offset so "tonight" is used until 15:00 UTC
    offset = 3 / 24
    return mjd_now - offset


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

    def __init__(self, design, scheduler=None, mjd_plan=None, position=None):
        if isinstance(design, targetdb.Design):
            self.designID = int(design.design_id)
            self.dbDesign = design
        else:
            self.designID = int(design)
            self.dbDesign = targetdb.Design.get(design_id=self.designID)
        self.field = self.dbDesign.field
        self.fieldID = self.field.field_id
        self.field_pk = self.field.pk
        self.ra = self.field.racen
        self.dec = self.field.deccen
        self.cadence = self.field.cadence.label
        # self.obsTimes = dict()
        self.haRange = [-60, 60]
        self.RS = scheduler
        self.mjd_plan = mjd_plan
        self.position = position

        cadence = self.field.cadence

        expCount = [np.sum(cadence.nexp[:i+1]) for i in range(len(cadence.nexp))]
        current_epoch = np.where(np.array(expCount) >= self.dbDesign.exposure)[0][0]
        self.obs_mode = cadence.obsmode_pk[current_epoch]

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
        # if we ever need more than a few, get this from
        # scheduler.fields array probably; all info should be there
        if isinstance(field, targetdb.Field):
            self.pk = int(field.pk)
            self.fieldID = int(field.field_id)
            self.dbField = field
        else:
            self.pk = int(field)
            self.dbField = targetdb.Field.get(pk=self.pk)
            self.fieldID = int(self.dbField.field_id)
        self.ra = self.dbField.racen
        self.dec = self.dbField.deccen
        self.SkyCoord = SkyCoord(self.ra*u.deg, self.dec*u.deg)
        self.cadence = self.dbField.cadence.label
        self._obsTimes = None
        self._startTime = None
        self._mjdDuration = None
        # in MJD, needed for rescheduling
        self.haRange = [-60, 60]
        self.RS = scheduler  # keep track. bad form?
        self.designs = list()
        # self.backups = list()

    def _timesFromDesigns(self):
        """startTime and obsTimes need to get info from designs
        """
        start = np.min([d.mjd_plan for d in self.designs])
        self._startTime = start
        startTime = Time(start, format="mjd").datetime,
        if type(startTime) is tuple:
            startTime = startTime[0]
        self._mjdDuration = len(self.designs) * design_time
        endTime = startTime + datetime.timedelta(seconds=int(self._mjdDuration*86400))
        self._obsTimes = {"start": startTime,
                          "end": endTime}

    @property
    def obsTimes(self):
        # datetime
        if self._obsTimes is None:
            self._timesFromDesigns()
        return self._obsTimes

    @property
    def startTime(self):
        # mjd
        if self._startTime is None:
            self._timesFromDesigns()
        return self._startTime

    @property
    def haPlanned(self):
        self.obsTimes
        end = self._startTime + self._mjdDuration
        haStart = self.RS.lst(self._startTime) - self.ra
        haEnd = self.RS.lst(end) - self.ra
        return (float(haStart), float(haEnd))

    @property
    def haNow(self):
        now = Time.now()
        now.format = "mjd"
        lst = self.RS.lst(now.value)
        return float(self.RS.ralst2ha(ra=self.ra, lst=lst))

    @property
    def utRange45DegZenith(self):
        if self.haRange45DegZenith is None:
            return None
        elif np.any([np.isnan(ha) for ha in self.haRange45DegZenith]):
            return None
        ha_pos = self.haRange45DegZenith[1]
        return self._zenAngleUTC(ha_pos)

    @property
    def haRange45DegZenith(self):
        return self._zenAngleHA(angle=45.)

    @property
    def utRange60DegZenith(self):
        if self.haRange60DegZenith is None:
            return None
        elif np.any([np.isnan(ha) for ha in self.haRange60DegZenith]):
            return None
        ha_pos = self.haRange60DegZenith[1]
        return self._zenAngleUTC(ha_pos)

    @property
    def haRange60DegZenith(self):
        return self._zenAngleHA(angle=60.)

    @property
    def utRange5DegZenith(self):
        if self.haRange5DegZenith is None:
            return None
        elif np.any([np.isnan(ha) for ha in self.haRange5DegZenith]):
            return None
        ha_pos = self.haRange5DegZenith[1]
        return self._zenAngleUTC(ha_pos)

    @property
    def haRange5DegZenith(self):
        # """Return the ha range for which this field has a zenith
        # angle of 5 degrees or less, or None
        # """
        return self._zenAngleHA(angle=5.)

    @property
    def utRange3DegZenith(self):
        if self.haRange3DegZenith is None:
            return None
        elif np.any([np.isnan(ha) for ha in self.haRange3DegZenith]):
            return None
        ha_pos = self.haRange3DegZenith[1]
        return self._zenAngleUTC(ha_pos)

    @property
    def haRange3DegZenith(self):
        # """Return the ha range for which this field has a zenith
        # angle of 3 degrees or less, or None
        # """
        return self._zenAngleHA(angle=3.)

    def _zenAngleHA(self, angle):
        """Return the ha range for which this field has a zenith
        angle of input angle(degrees) or less, or None
        """
        ha = Site.zenithAngleHA(self.dec, zenithAngle=angle)
        if ha == 0:
            return None
        else:
            return (-ha, ha)

    def _zenAngleUTC(self, ha):

        return Site.targetHa2UTC(ha, target=self.SkyCoord, mjd=self.startTime)


class Queue(object):
    """wrapper around opsdb.Queue
    """

    def __init__(self):
        self.scheduler = Scheduler()
        self.queue = opsdb.Queue
        # wrap blocking this is a DB call
        self.dbDesigns = self.queue.select()\
                                   .where(opsdb.Queue.position > -3)\
                                   .order_by(opsdb.Queue.position)
        # or it might be here
        self.designs = [Design(d.design.design_id,
                               scheduler=self.scheduler.scheduler,
                               mjd_plan=d.mjd_plan,
                               position=d.position)
                        for d in self.dbDesigns]
        self.fields = list()
        self._fieldDict = None

        for d in self.designs:
            if d.field_pk not in [f.pk for f in self.fields]:
                self.fields.append(Field(d.field,
                                         scheduler=self.scheduler.scheduler))
                self.fields[-1].designs.append(d)
            else:
                w = np.where(d.field_pk == np.array([f.pk for f in self.fields]))
                self.fields[int(w[0])].designs.append(d)

    @property
    def fieldDict(self):
        if self._fieldDict is None:
            self._fieldDict = {f.pk: f for f in self.fields}
        return self._fieldDict


class DesignList(object):
    """Container for a list of designs, primarily for investigating viz windows
    """

    def __init__(self, design_ids=[], mjd=None):
        self.scheduler = Scheduler()
        # wrap blocking this is a DB call
        # or it might be here
        dbDesign = targetdb.Design
        dbDesigns = dbDesign.select().where(dbDesign.design_id << design_ids)
        self.designs = [Design(d.design_id,
                               scheduler=self.scheduler.scheduler,
                               mjd_plan=mjd)
                        for d in dbDesigns]
        self.fields = list()

        for d in self.designs:
            if d.field_pk not in [f.pk for f in self.fields]:
                self.fields.append(Field(d.field,
                                         scheduler=self.scheduler.scheduler))
                self.fields[-1].designs.append(d)
            else:
                w = np.where(d.field_pk == np.array([f.pk for f in self.fields]))
                self.fields[int(w[0])].designs.append(d)


# singleton may not be necessary, but it is probably helpful
class Scheduler(object, metaclass=SchedulerSingleton):
    """Facilitate scheduling during the night. roboscheduler picks the best
    field for a given time, so this scheduler iterates through time to plan
    full or partial nights.
    """

    def __init__(self, **kwargs):
        self.plan = rs_version
        self.scheduler = roboscheduler.scheduler.Scheduler(observatory=observatory.lower())

        # wrap blocking this is a DB call
        self.scheduler.initdb(designbase=self.plan, fromFits=False)
        self.exp_nom = 18 / 60 / 24

    async def choiceFields(self, mjd, exp=12, oldPos=None):
        """return multiple fields for user to choose from
           at a specific mjd

        Parameters:
        ----------

        mjd : float
            the mjd to ask the scheduler to schedule for

        exp : integer
            how many exposures to schedule for (i.e. how much time do we have?)
        """
        # re-cache fields in case priorities changed
        await wrapBlocking(self.scheduler.fields.fromdb)

        if exp < 4:
            exp = 4
        field_pks, designs = await wrapBlocking(self.scheduler.nextfield,
                                                mjd=mjd,
                                                maxExp=exp,
                                                live=True,
                                                returnAll=True)
        fields = list()
        # design_count = list()
        if oldPos is not None:
            coords = [[oldPos[0], oldPos[1]]]
        else:
            coords = list()
        for f, d in zip(field_pks, designs):
            await asyncio.sleep(0)
            if len(fields) > 3:
                continue
            # try to fit in this slot as closely as possible
            # if abs(d - exp) > 2:
            #     continue
            idx = np.where(self.scheduler.fields.pk == f)
            ra = self.scheduler.fields.racen[idx]
            dec = self.scheduler.fields.deccen[idx]
            far_enough = True
            for c in coords:
                await asyncio.sleep(0)
                d = ((c[0] - ra)*np.cos(dec*np.pi/180))**2 + (dec - c[1])**2
                if d < 45**2:
                    far_enough = False
                    break
            if far_enough:
                fields.append(f)
                # design_count.append(d)
                coords.append([ra, dec])

        dbField = targetdb.Field
        id_query = await wrapBlocking(dbField.select(dbField.pk, dbField.field_id,
                                                     dbField.racen, dbField.deccen).where,
                                      dbField.pk << fields)
        field_pks = [q.pk for q in id_query]
        field_ids = [q.field_id for q in id_query]
        coords = [[q.racen, q.deccen] for q in id_query]

        return field_ids, coords, field_pks

    async def replaceField(self, oldField, backup):
        """replace oldField with backup in the queue

        Parameters:
        ----------

        oldField : integer
            the old field to be repalced

        backup : integer
            the new field to replace oldField
        """
        # re-cache fields in case priorities changed
        await wrapBlocking(self.scheduler.fields.fromdb)

        newDesigns = await wrapBlocking(self.scheduler.designsNext, backup)

        oldPositions = await wrapBlocking(opsdb.Queue.rm, oldField, returnPositions=True)

        Field = targetdb.Field
        Design = targetdb.Design
        Version = targetdb.Version
        dbVersion = await wrapBlocking(Version.get, plan=self.plan)
        designs = await wrapBlocking(Design.select().join(Field).where,
                                     Field.pk == backup,
                                     Field.version == dbVersion,
                                     Design.exposure << newDesigns)

        queuePos = min(oldPositions)
        for d in designs:
            await asyncio.sleep(0)
            await wrapBlocking(opsdb.Queue.insertInQueue, d, queuePos)
            queuePos += 1

    async def queueFromSched(self, mjdStart, mjdEnd):
        """Schedule the night from mjdStart to mjdEnd and populate the queue
        with those designs.

        Parameters:
        ----------

        mjdStart : float
            the MJD start time

        mjdStop : float
            the MJD stop time
        """
        # re-cache fields in case priorities changed
        await wrapBlocking(self.scheduler.fields.fromdb)

        now = mjdStart

        queue = await wrapBlocking(Queue)

        inQueue = [f.pk for f in queue.fields]

        Field = targetdb.Field
        Design = targetdb.Design
        Version = targetdb.Version
        dbVersion = await wrapBlocking(Version.get, plan=self.plan)

        errors = list()

        while now < mjdEnd:
            await asyncio.sleep(0)
            exp_max = (mjdEnd - now) // self.exp_nom
            # field id and exposure nums of designs
            field_pk, designs = await wrapBlocking(self.scheduler.nextfield,
                                                   mjd=now,
                                                   maxExp=exp_max,
                                                   live=True,
                                                   ignore=inQueue)

            if field_pk is None:
                errors.append(unfilledMjdError(now))
                now += self.exp_nom
                continue
            designs = await wrapBlocking(Design.select().join(Field).where,
                                         Field.pk == field_pk,
                                         Field.version == dbVersion,
                                         Design.exposure << designs)
            for i, d in enumerate(designs):
                await asyncio.sleep(0)
                mjd_plan = now + i * self.exp_nom
                await wrapBlocking(opsdb.Queue.appendQueue, d, mjd_plan)

            inQueue.append(field_pk)

            now += len(designs) * self.exp_nom

        tstamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        self.scheduler.priorityLogger.write(name=tstamp)

        return errors

    async def schedNoQueue(self, mjdStart, mjdEnd):
        """Schedule the night from mjdStart to mjdEnd but DO NOT populate
        the queue. For planning.

        Parameters:
        ----------

        mjdStart : float
            the MJD start time

        mjdStop : float
            the MJD stop time
        """
        # re-cache fields in case priorities changed
        await wrapBlocking(self.scheduler.fields.fromdb)

        now = mjdStart

        inQueue = list()

        fields = list()

        errors = list()

        while now < mjdEnd:
            await asyncio.sleep(0)
            exp_max = (mjdEnd - now) // self.exp_nom
            # field id and exposure nums of designs
            # field_id, designs = self.scheduler.nextfield(mjd=now,
            #                                              maxExp=exp_max,
            #                                              live=True,
            #                                              ignore=inQueue)
            field_pk, designs = await wrapBlocking(self.scheduler.nextfield,
                                                   mjd=now,
                                                   maxExp=exp_max,
                                                   live=True,
                                                   ignore=inQueue)
            if field_pk is None:
                errors.append(unfilledMjdError(now))
                now += self.exp_nom
                continue

            inQueue.append(field_pk)

            field_wrap = await wrapBlocking(Field, field_pk, self.scheduler)
            # manually, to save us from designs
            field_wrap._startTime = now

            startTime = Time(now, format="mjd").datetime
            mjd_duration = len(designs) * design_time
            endTime = startTime + datetime.timedelta(seconds=int(mjd_duration*86400))
            field_wrap._obsTimes = {"start": startTime,
                                    "end": endTime}

            field_wrap._mjdDuration = mjd_duration

            fields.append(field_wrap)

            now += len(designs) * self.exp_nom
        tstamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        fname = "lookAhead" + tstamp

        self.scheduler.priorityLogger.write(name=fname)

        return fields, errors

    def getDarkBounds(self, mjd):
        """find the beginning and end of the night

        Parameters:
        ----------

        mjd : numeric
            the MJD day we want bounds for
        """
        mjd_evening_twilight = self.scheduler.evening_twilight(mjd=mjd, twilight=-15)
        mjd_morning_twilight = self.scheduler.morning_twilight(mjd=mjd, twilight=-15)
        return mjd_evening_twilight, mjd_morning_twilight

    def getNightBounds(self, mjd):
        """find the beginning and end of the night

        Parameters:
        ----------

        mjd : numeric
            the MJD day we want bounds for
        """
        mjd_evening_twilight = self.scheduler.evening_twilight(mjd)
        mjd_morning_twilight = self.scheduler.morning_twilight(mjd)
        return mjd_evening_twilight, mjd_morning_twilight

    async def rescheduleAfterField(self, field_pk, night_end):
        """reschedule the rest of the night starting with fieldID

        Parameters:
        ----------

        fieldID : integer
            the field to begin rescheduling the night at

        night_end : float
            the MJD of the end of the night; the beginning will be the
            scheduled mjd of fieldID
        """
        queue = await wrapBlocking(Queue)

        field = queue.fieldDict[field_pk]
        mjd_prev = field.startTime

        rm_fields = [f for f in queue.fields if f.startTime >= mjd_prev]

        for f in rm_fields:
            await asyncio.sleep(0)
            await wrapBlocking(opsdb.Queue.rm, f.pk)

        return await self.queueFromSched(mjd_prev, night_end)


def unfilledMjdError(mjd):
    return f"could not schedule field at {mjd}"
