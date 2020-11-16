import datetime
import itertools

import numpy
import astropy.units as u
from astropy.coordinates import EarthLocation, AltAz, get_sun, get_moon

def wrapHA(ha):
    """Force ha into range -180 to 180. Just to be sure.
    """
    if -180<ha<=180:
        return ha
    while ha > 180:
        ha = ha - 360.
    while ha <= -180:
        ha = ha + 360.
    assert -180<ha<=180, "ha = %.2f"%ha
    return ha

class APOSite(object):
    lat = 32.789278
    lon = -105.820278
    altitude = 2788
    # site = pyobs.Site(lat, -105.820278, alt=altitude)
    APO = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=altitude*u.m)
    # sun = ephem.Sun()
    # moon = ephem.Moon()
    # ephAPO = ephem.Observer()
    # ephAPO.lon = '254.180000305'
    # ephAPO.lat = '32.7899987793' # this doesnt exactly match pyobs?
    # ephAPO.lat = '32.789278'
    #ephAPO.elevation = set it?


    @classmethod
    def zenithWarnHA(cls, dec, zenithAngle):
        """Return hour angle (degrees) at which a given declination (dec, degrees) will fall within zenithAngle (degrees from zenith at APO)
        """
        # don't bother doing any work if dec never comes within zenithAngle of zenith at apo
        if numpy.abs(dec - cls.lat) > zenithAngle:
            # spherical trig is tricky, check that this is valid?
            return 0
        # numpy routines use radians:
        zenithAngleRad = numpy.radians(zenithAngle)
        decRad = numpy.radians(90. - dec)
        siteLatRad = numpy.radians(90. - cls.lat) # spherical coords, polar angle is zero at [0 0 1]
        # use the fact that cos(angle) = A dot B.  A and B are unit vectors in cartesian coords.
        # solve for HA which is hidden in B via (A dot B) = cos(zenithAngle)
        # strategy: convert zenith vector at APO into unit cartesian coord, call it A:
        # A = [sin(apoLatitude) 0 cos(apoLatitude)]
        # create unit cartesian vector B containing HA an unknown to solve for, at fixed declination dec.
        # B = [cos(HA)*sin(dec) sin(HA)*sin(dec) cos(dec)]
        # dot them together: cos(zenithAngle) = A dot B
        # cos(zenithAngle) = sin(apoLatitude)*cos(HA)*sin(dec) + cos(apoLatitude)*cos(dec)
        # isolate HA
        HA = numpy.arccos((numpy.cos(zenithAngleRad) - numpy.cos(siteLatRad)*numpy.cos(decRad)) / (numpy.sin(siteLatRad)*numpy.sin(decRad)))
        # and we want degrees
        return numpy.degrees(HA)

    # @classmethod
    # def getVizTimesUTC(cls, mjd, ra, haRange, haNominal=None):
    #     """Return datetime (UTC) objects representing beginning, nominal, and end
    #     times for a visibility window, for a given MJD.
    #     """
    #     assert len(haRange) == 2
    #     minHA = wrapHA(haRange[0])
    #     maxHA = wrapHA(haRange[1])
    #     # if nominal wasn't provided use the midpoit of haRange
    #     if haNominal is None:
    #         haNominal = numpy.mean(numpy.asarray([minHA, maxHA])) # will be wrapped
    #     else:
    #         haNominal = wrapHA(haNominal)
    #     # insert nominal into the haList
    #     haList = [minHA, haNominal, maxHA]
    #     assert haList[0]<=haList[1]<=haList[2]
    #     # get date for window
    #     # date = cls.mjd2DatetimeUTC(mjd).date()
    #     # print("viz time mjd: %.2f"%mjd)
    #     timeList = ["min", "nominal", "max"]
    #     timeDict = {}
    #     for ha, key in itertools.izip(haList, timeList):
    #         # lst = (ha + ra) % 360 / 15.0
    #         # utcDatetime = cls.site.localTime(lst, date=date.date(), utc=True, returntype="datetime").replace(tzinfo=None)
    #         # timeDict[key] = datetime.datetime(utcDatetime.year, utcDatetime.month, utcDatetime.day, utcDatetime.hour, utcDatetime.minute, utcDatetime.second)
    #         timeDict[key] = cls.ha2DatetimeUTC(mjd, ra, ha)
    #     # correct for dates crossing the day line
    #     # there is probably a more robust way to determine this.
    #     if timeDict["min"] > timeDict["nominal"]:
    #         timeDict["min"] = timeDict["min"] + datetime.timedelta(days=-1)

    #     if timeDict["max"] < timeDict["nominal"]:
    #         timeDict["max"] = timeDict["max"] + datetime.timedelta(days=+1)

    #     return timeDict

    # this method causes trouble, its not used much, lets try to get around it
    # @classmethod
    # def ha2DatetimeUTC(cls, mjd, ra, ha):
    #     date = sdssconv.mjd2datetime(mjd).date() # only date will be used.
    #     lst = (ha + ra) % 360 / 15.0
    #     utcDatetime = cls.site.localTime(lst, date=date, utc=True, returntype="datetime").replace(tzinfo=None)
    #     return utcDatetime

    @classmethod
    def mjd2lst(cls, MJD):
        """return lst in decimal hours
        """
        return cls.site.localSiderialTime(2400000 + MJD)

    # @classmethod
    # def mjd2DatetimeUTC(cls, MJD):
    #     """Convert decimal hour MJD value to UTC
    #     @param[in] MJD: float, decimal hours
    #     @return a datetime object (UTC)
    #     """
    #     # print("mjd2datetimemjd: %.2f"%MJD)
    #     # lst = cls.site.localSiderialTime(2400000 + MJD)
    #     lst = cls.mjd2lst(MJD)
    #     # something isn't completely correct here. moon needs - 0, timebars need - 0.5
    #     # this probably means mjd is defined in multiple ways in sub-components. 
    #     # hack around this for now
    #     dt1 = sdssconv.mjd2datetime(MJD - 0.5) # use this to get correct date, AS give mjd -.5
    #     # print("mjd2datetimemjd date: %s"%str(dt1))
    #     dt2 = cls.site.localTime(lst, date=dt1.date(), returntype="datetime", utc=True).replace(tzinfo=None)
    #     # dt3 = datetime.datetime(dt2.year, dt2.month, dt2.day, dt2.hour, dt2.minute, dt2.second)
    #     return dt2

    @classmethod
    def lstMidnight(cls, datetimeObj=None, returntype="datetime"):
        if not datetimeObj:
            datetimeObj = datetime.datetime.now()
        dateObj = datetimeObj.date()
        return cls.site.localSiderialTime(dateObj, returntype=returntype)
        # else:
        #     return cls.site.localSiderialTime(returntype="datetime")

    @classmethod
    def raDec2AltAz(cls, ra, dec):
        """Convert from RA, DEC to Alt Az
        @return tuple (alt, az) in degrees.
        """
        platecoo = pycoo.ICRSCoordinates(ra, dec)
        coords = cls.site.apparentCoordinates(platecoo)
        return (coords.alt.d, coords.az.d)

    @classmethod
    def ra2ha(cls, ra):
        ha = float(15.0 * cls.site.localSiderialTime() - ra)
        while ha < -180:
            ha += 360
        while ha > 180:
            ha -= 360
        return ha

    @classmethod
    def sunRiseAndSet(cls, mjd):
        """@param[in] date, a datetime obj or None
        """
        return cls._riseAndSet(cls.sun, horizon=0, mjd=mjd, useCenter=True)

    @classmethod
    def twilightRiseAndSet(cls, mjd, degree):
        return cls._riseAndSet(cls.sun, horizon=-1*degree, mjd=mjd, useCenter=True)

    @classmethod
    def moonRiseAndSet(cls, mjd):
        # print("moon rise and set")
        return cls._riseAndSet(cls.moon, horizon=0, mjd=mjd, useCenter=True)

    @classmethod
    def moonphase(cls, mjd):
        # get moonphase for midpoint between sun rise and set for a given datetime
        # if none date is now
        return idlasl.moonphase(numpy.mean([cls._ephem2jd(x) for x in cls.sunRiseAndSet(mjd)]))

    @classmethod
    def moondistance(cls, ra, dec, mjd=None):
        """Compute angular distance in degrees between moon position computed
        at the given mjd to the supplied ra and dec.

        Handled by IDLASL and astrophysics, same algorithm as autoscheduler
        Thanks to Ben Thompson.
        """
        if not mjd:
            date = datetime.datetime.now()
            jd = sdssconv.datetime2jd(date) # or maybe mjd should be used?
        else:
            jd = sdssconv.mjd2jd(mjd)
        moonpos = idlasl.moonpos(jd)
        moonpos = pycoo.ICRSCoordinates(moonpos[0], moonpos[1])
        targetcoords = pycoo.ICRSCoordinates(ra, dec)
        return (moonpos - targetcoords).d

    @classmethod
    def _riseAndSet(cls, obj, horizon, mjd, useCenter=True):
        date = cls.mjd2DatetimeUTC(mjd + 0.5) # + 0.5 to hack around multiple mjd definitons problem
        cls.ephAPO.horizon = str(horizon)
        cls.ephAPO.date = (date.year, date.month, date.day, date.hour, date.minute, date.second) # moon wrong?
        objSet = cls.ephAPO.previous_setting(obj, use_center=useCenter).tuple()
        objRise = cls.ephAPO.next_rising(obj, use_center=useCenter).tuple()
        return (objRise, objSet)

    @staticmethod
    def _ephem2jd(obj):
        return sdssconv.ymd2jd(obj[0], obj[1], obj[2]) + (obj[3] + obj[4]/60. + obj[5]/3600.)/24.
