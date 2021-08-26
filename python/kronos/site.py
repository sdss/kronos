import datetime
import itertools

import numpy
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import SkyCoord, AltAz, get_sun, get_moon
from astroplan import Observer

from kronos import observatory

def wrapHA(ha):
    """Force ha into range -180 to 180. Just to be sure.
    """
    if -180 < ha <= 180:
        return ha
    while ha > 180:
        ha = ha - 360.
    while ha <= -180:
        ha = ha + 360.
    assert -180 < ha <= 180, "ha = {:.2f}".format(ha)
    return ha


class Site(object):
    # lat = 32.789278

    if observatory == "APO":
        site = Observer.at_site("APO", timezone="US/Mountain")
    else:
        site = Observer.at_site("LCO", timezone="America/Santiago")

    lat = site.location.lat.deg

    @classmethod
    def zenithAngleHA(cls, dec, zenithAngle):
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

    @classmethod
    def targetHa2UTC(cls, ha, **kwargs):
        t_time = cls.transitTime(**kwargs).datetime
        ha_hours = ha / 15.
        delta = datetime.timedelta(hours=ha_hours)
        return (t_time - delta, t_time + delta)

    @classmethod
    def transitTime(cls, target=None, ra=None, dec=None, mjd=None, time=None):
        """calculate transit time for an object using astroplan.observer

           target : astropy.SkyCoord
           ra, dec: degrees, if no target is given
           time : an astropy time
           mjd : if no time is given, if neither now is used
        """

        if time is None:
            if mjd is not None:
                time = Time(mjd, format="mjd")
            else:
                time = Time.now()

        if target is None:
            assert ra is not None, "must specify coords if targ not given"
            assert dec is not None, "must specify coords if targ not given"
            target = SkyCoord(ra*u.deg, dec*u.deg)

        # which means relative to sunrise, "nearest" seems to work best
        t_time = cls.site.target_meridian_transit_time(time, target, which="nearest")

        return t_time

    @classmethod
    def mjd2lst(cls, MJD):
        """return lst in decimal hours
        """
        return cls.site.localSiderialTime(2400000 + MJD)

    # @classmethod
    # def lstMidnight(cls, datetimeObj=None, returntype="datetime"):
    #     if not datetimeObj:
    #         datetimeObj = datetime.datetime.now()
    #     dateObj = datetimeObj.date()
    #     return cls.site.localSiderialTime(dateObj, returntype=returntype)
    #     # else:
    #     #     return cls.site.localSiderialTime(returntype="datetime")

    # @classmethod
    # def raDec2AltAz(cls, ra, dec):
    #     """Convert from RA, DEC to Alt Az
    #     @return tuple (alt, az) in degrees.
    #     """
    #     platecoo = pycoo.ICRSCoordinates(ra, dec)
    #     coords = cls.site.apparentCoordinates(platecoo)
    #     return (coords.alt.d, coords.az.d)

    @classmethod
    def moonRiseSet(cls, mjd_evening_twilight):
        """calculate moon rise and set appropriately after mjd_evening_twilight
        """
        time = Time(mjd_evening_twilight, format="mjd")
        moon_pos = cls.site.moon_altaz(time)
        if moon_pos.alt.value > 0:
            moon_set = cls.site.moon_set_time(time, which="next")
            moon_rise = cls.site.moon_rise_time(time, which="previous")
        else:
            moon_set = cls.site.moon_set_time(time, which="next")
            moon_rise = cls.site.moon_rise_time(time, which="next")
        return moon_rise.datetime, moon_set.datetime
