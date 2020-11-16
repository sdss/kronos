"""Contains construction classes/functions to fully define a vizualization.
A python interface/bridge to the D3/JS.  The goal of these helpers is to catch
potential errors before implementing the JS.  Also greatly simplifies the JS/D3.
"""
import datetime
from collections import OrderedDict
import numpy

from kronos.scheduler import Scheduler


class SVGAttrs(object):
    def __init__(self, color, opacity):
        self.fill = color
        self.opacity = opacity
        self.rx = 5 # bar edge radius
        self.ry = 5 # bar edge radius

svgAttrDict = { # colors that svg knows about
    "grey": SVGAttrs("black", 0.2),
    "background": SVGAttrs("white", 1.),
    "backgroundset": SVGAttrs("green", .3),
    "twilight": SVGAttrs("teal", 0.1),
    "apogee": SVGAttrs("#191919", 0.5),
    "vizwindow": SVGAttrs("blue", 0.5),
    "missing": SVGAttrs("yellow", 1.0),
    "infobar": SVGAttrs("black", 0.6),
    "ha": SVGAttrs("teal", 0.1),
    "zwarn1": SVGAttrs("chocolate", 0.8),
    "zwarn2": SVGAttrs("red", 0.8),
}

# define what shows up in the table (in what order too)
# commonTableItems = ["cart", "plate", "ra", "dec", "UT1", "UT2", "currAlt"] #, "platePriority", "moonDist", , ]
# bossChannels = ["b1 (SN)", "r1 (SN)", "b2 (SN)", "r2 (SN)"]
# ebossTableItems = commonTableItems + bossChannels #+ [x+" (%)" for x in bossChannels]
# apogeeTableItems = commonTableItems + ["name", "startUT", "expLength", "visits", "S/N", "done (%)"]
# mangaTableItems = commonTableItems + ["sets"] + bossChannels + ["done"] #+ [x+" (SN)" for x in bossChannels]
# mangaSetTableItems = ["utc-range", "seeing", "missing"] #+ bossChannels #+ [x+" (SN)" for x in bossChannels]

# newTableItems = ["cart", "plate", "ra", "dec", "currHA", "UTMid"]
# planTableItems = ["plate", "ra", "dec", "priority", "done"]


def datetime2dict(datetimeObj):
    """Return a dictionary keyed by year, month, day, hour, second, millisecond.
    This type of dictionary is used to create javascript Date objects
    """
    if datetimeObj is None:
        return None
    return {
        "year": datetimeObj.year,
        "month": datetimeObj.month,
        "day": datetimeObj.day,
        "hour": datetimeObj.hour,
        "minute": datetimeObj.minute,
        "second": datetimeObj.second,
        "ms": 0,
    }

def verifyUTRange(utRange, name="?"):
    """inputs:
    utRange (datetime, datetime)
    name: str, name for error reporting
    """
    # verify that the datetimes make sense
    assert len(utRange) == 2, "utRange fail for %s"%name
    for dt in utRange:
        assert type(dt) == datetime.datetime, "utRange fail for %s"%name
    assert utRange[0] <= utRange[1], "utRange fail for %s, ut1: %s, ut2: %s"%(name, str(utRange[0]), str(utRange[1]))
    # verify the range is less than a day, (otherwise something is wrong)
    assert (utRange[1]-utRange[0]).days == 0, "utRange fail for %s"%name

class VizWindow(object):
    """Represents a time/ha window
    """
    def __init__(self, name, utRange, haRange, primary=False, text=None):
        """inputs:
        name:
        utRange: (datetimeStart, datetimeEnd)
        haRange: (degrees, degrees)
        text: str, or None.  If not None, overlay this text.
        """
        self.svgAttr = svgAttrDict[name.lower()]
        self.utRange = utRange
        self.haRange = haRange
        self.text = text
        self.primary = primary

    @property
    def showUT(self):
        if self.utRange[0]==self.utRange[1]:
            return False
        else:
            return True

    @property
    def showHA(self):
        if self.haRange[0]==self.haRange[1]:
            return False
        else:
            return True

    def export(self):
        """Pack up info for jsonification
        """
        return {
            "fill": self.svgAttr.fill,
            "opacity": self.svgAttr.opacity,
            "rx": self.svgAttr.rx,
            "ry": self.svgAttr.ry,
            "utRange": [datetime2dict(datetimeObj) for datetimeObj in self.utRange],
            "haRange": list(self.haRange),
            "text": self.text,
            "showUT": self.showUT,
            "showHA": self.showHA,
            "primary": self.primary
        }

class TimeScale(object):
    def __init__(self, utRange):
        """inputs:
        utRange: (datetimeStart, datetimeEnd) endpoints of timescale
        """
        verifyUTRange(utRange, "timescale")
        self.range = utRange

    def export(self):
        # print("time scale", self.range)
        return [datetime2dict(datetimeObj) for datetimeObj in self.range]

class HAScale(object):
    def __init__(self, haRange):
        """inputs:
        haRange: (min, max) hour angle degrees
        """
        assert len(haRange) == 2
        assert haRange[0] < haRange[1]
        self.range = haRange

    def export(self):
        return list(self.range)

class VizRow(object):
    def __init__(self, field, tableDict, timeScale, haScale, setCurrent=True, isHeader=False, isChild=False):
        """inputs:
        field: a scheduler.field object
        tableDict: dictionary that corresponds to keys/values wanted for tabular display
        timeScale: an instance of TimeScale
        haScale: an instance of HAScale
        setCurrent: bool, if True get the current (now!) time and HA (consider renaming to planning/observing?)
        isHeader: bool, if True this is the top row (should display schedule and table headers)
        """
        self.field = field
        self.tableKeys = list(tableDict.keys()) # used by header row
        self.tableValues = tableDict.values()
        self.timeScale = timeScale
        self.haScale = haScale
        self.currentTime, self.currentHA = None, None
        self.setCurrent = setCurrent
        if setCurrent:
            self.setCurrentMarkers()
        self.vizWindows = []
        self.isHeader = isHeader
        self.isChild = isChild
        self.hasChild = False


    def addVizWindow(self, name, utRange, haRange, primary=False, text=None):
        """viz windows drawn in order added (so last will lay 'above' first)"""
        if utRange is not None:
            # none is allowed
            verifyUTRange(utRange, name)
            utRange = list(utRange) # for potential item assignment, ranges are tuples
        if haRange is not None:
            haRange = list(haRange)
        # handle cases where viz window is partially or fully outside time scale
        if utRange is None or (utRange[0] > self.timeScale.range[1]) or (utRange[1] < self.timeScale.range[0]):
            if utRange is not None:
                print("WARNING viz window %s completely outside time scale!"%name)
            # set range values equal to each other
            utRange = (self.timeScale.range[0], self.timeScale.range[0])
        if utRange[1] > self.timeScale.range[1]:
            utRange[1] = self.timeScale.range[1]
        if utRange[0] < self.timeScale.range[0]:
            utRange[0] = self.timeScale.range[0]

        # handle cases where viz window is partially or fully outside ha scale
        # this should probably never be an issue
        if haRange is None or (haRange[0] > self.haScale.range[1]) or (haRange[1] < self.haScale.range[0]):
            if haRange is not None:
                print("WARNING viz window %s completely outside ha scale!"%name)
            # set range values equal to each other
            haRange = (self.haScale.range[0], self.haScale.range[0])
        if haRange[1] > self.haScale.range[1]:
            haRange[1] = self.haScale.range[1]
        if haRange[0] < self.haScale.range[0]:
            haRange[0] = self.haScale.range[0]

        self.vizWindows.append(VizWindow(name, tuple(utRange), tuple(haRange), primary, text))


    def addChildViz(self, vizObj):
        """vizObj, instance of Viz (probably MangaSetViz)
        """
        self.childViz = vizObj
        self.hasChild = True


    def setCurrentMarkers(self):
        """establish positions for current time and HA, if they
        fall within the ut/ha scale range
        """
        currentTime = datetime.datetime.utcnow()
        currentHA = self.field.haNow
        if self.timeScale.range[0]<=currentTime<=self.timeScale.range[1]:
            # marker falls inside time scale
            self.currentTime = currentTime
        if self.haScale.range[0]<=currentHA<=self.haScale.range[1]:
            # marker falls inside time scale
            self.currentHA = currentHA


    def export(self):
        # look for float table values, convert them to strings.
        tableValues = []
        for value in self.tableValues:
            if type(value) == float:
                value = "%.2f"%value
            tableValues.append(value)
        return {
            "fieldID": self.field.fieldID,
            "tableItems": self.tableKeys if self.isHeader else tableValues,
            "vizWindows": [vizWindow.export() for vizWindow in self.vizWindows],
            "currentTime": datetime2dict(self.currentTime),
            "currentHA": self.currentHA, # used for current HA marker (may be None)
            "expanded": False, # flag, to be used in d3/J
            "selected": False, # flag, to be used in d3/J
            "autoscheduled": True,
            "coPlugged": False,
            "yValue": 0., # initialize all rows to lie at y=0 (JS will update)
            "childViz": self.childViz.export() if self.hasChild else None,
            "isChild": self.isChild,
            "isHeader": self.isHeader,
            "hasChild": self.hasChild,
            "trueHA": self.field.haNow, # used for real time altitude display in Petunia (may not be None)
            "dec": self.field.dec,
            "isSpecial": False,
            "setCurrent": self.setCurrent,
            "surveyMode": "",
            "timeScale": self.timeScale.export()
            # "alt": -99,  # for updating in JS
            # "az": -99,  # for updating in JS
        }

class Viz(object):
    def __init__(self, schedule, fieldList, setCurrent=True, isChild=False, surveyName=None):
        """schedule: output from Autoscheduler.getSchedulerObsDict()
        plateList: a list of dbWrappers.Plate objects, displayed in list order (not sorted here)
        setCurrent: bool, if True, current time/HA markers will be indicated, false for planning
            [consider renaming this parameter to planning or someting?]
        """
        self.surveyName = surveyName
        self.isChild = isChild
        self.haScale = HAScale((-4*15, 4*15))
        self.schedule = schedule
        self.mjd = schedule["queriedMJD"]
        self.fieldList = fieldList
        self.setCurrent = setCurrent
        self.timeScale = TimeScale((schedule["timeBarStartUTC"], schedule["timeBarEndUTC"]))
        self.fieldRows = []
        if not self.isChild:
            self.fieldRows.append(self.getHeaderRow())
        self.fieldRows.extend(self.getFieldRows())

    def getTableDict(self, field):
        """Return a dictionary.  Keys displayed as table headers, values: displayed in table.
        """

        tableDict = OrderedDict((
            ("field", field.fieldID),
            ("currHA", field.haNow),
            ("alt", -999),
            ("utc-start", field.obsTimes["start"].strftime("%H:%M")),
        ))
        # else:
        #     # not current (survey planning), no time-now, choose elements to display
        #     if self.surveyName == "eboss":
        #         complete = plate.bossCompletionPercent
        #     elif self.surveyName == "apogee":
        #         if plate.apogeeCompletion is not None:
        #             # occasionally apogee completion calculation fails, usually due to missing db
        #             # elements.  Keep petunia from crashing here
        #             complete = "%.2f " % plate.apogeeCompletion
        #         else:
        #             complete = "??"
        #     else:
        #         assert self.surveyName == "manga"
        #         complete = " %.2f " % plate.mangaCompletion
        #     tableDict = OrderedDict((
        #         ("cart", cart),
        #         ("plate", plate.plateID),
        #         ("ra", plate.ra),
        #         ("dec", plate.dec),
        #         ("ha", plate.ha),
        #         ("priority", plate.priority),
        #         ("beg", vizTimes["min"].strftime("%H:%M")),
        #         ("end", vizTimes["max"].strftime("%H:%M")),
        #         ("%", complete),
        #     ))

        if not hasattr(self, "nTableItems"):
            self.nTableItems = len(tableDict) # set length
        return tableDict

    def exportAllRows(self):
        allRows = []
        for row in self.fieldRows:
            if row.hasChild: # place children in front (so they are drawn first)
                allRows.extend([r.export() for r in row.childViz.fieldRows])
            allRows.append(row.export())
        return allRows

    @property
    def hasChild(self):
        # slow, linear search
        hasChild = False
        for row in self.fieldRows:
            if row.hasChild:
                hasChild = True
                break
        return hasChild

    @property    
    def nChildTableItems(self):
        nChildTableItems = 0
        if self.hasChild:
            for row in self.fieldRows:
                if row.hasChild:
                    nChildTableItems = row.childViz.nTableItems
                    break
        return nChildTableItems

    def export(self):
        # print(self.surveyName, self.isChild)
        return {
            "haScale": self.haScale.export(),
            "timeScale": self.timeScale.export(),
            "plateRows": [fieldRow.export() for fieldRow in self.fieldRows],
            "allRows": self.exportAllRows(),
            "isChild": self.isChild,
            "hasChild": self.hasChild,
            "nTableItems": self.nTableItems, # define length of side table
            "setCurrent": self.setCurrent,
            "nChildTableItems": self.nChildTableItems
            }

    def getHeaderRow(self):
        headerRow = VizRow(self.fieldList[0], self.getTableDict(self.fieldList[0]), self.timeScale, self.haScale, self.setCurrent, isHeader=True, isChild=self.isChild)
        headerRow.addVizWindow( # draw on a white background, do overlapping bars with opacity don't bleed
            name = "background",
            utRange = self.timeScale.range,
            haRange = self.haScale.range
        )
        if not "morningTwilightUTC" in self.schedule:
            headerRow.addVizWindow( # draw on a white background, do overlapping bars with opacity don't bleed
                name = "background",
                utRange = self.timeScale.range,
                haRange = self.haScale.range,
                text="add twilight..."
            )
        else:
            # add twilight bars
            headerRow.addVizWindow(
                name = "twilight",
                utRange=(self.schedule["timeBarStartUTC"], self.schedule["eveningTwilightUTC"]),
                haRange=None,
                text="twilight"
            )
            headerRow.addVizWindow(
                name = "twilight",
                utRange=(self.schedule["morningTwilightUTC"], self.schedule["timeBarEndUTC"]),
                haRange=None,
                text="twilight"
            )
            # add in scheduled survey times
            if self.schedule["apogeeStartUTC"] is not None:
                headerRow.addVizWindow(
                    name = "apogee",
                    utRange = (self.schedule["apogeeStartUTC"], self.schedule["apogeeEndUTC"]),
                    haRange=None,
                    text = "Apogee"
                )
            # create ha bar
            headerRow.addVizWindow(
                name = "ha",
                utRange = None,
                haRange = self.haScale.range, # full range
                text = "HA"
            )
        return headerRow

    def getFieldRows(self):
        """surveyName"""
        fieldRows = []
        for field in self.fieldList:
            row = self._basicFieldRow(field)
            if not self.isChild:
                row.addChildViz(childViz(self.schedule, field.backups))
            fieldRows.append(row)
        return fieldRows

    def _basicFieldRow(self, field):
        """field: dbWrappers.field instance
        """

        fieldHaRange = field.haRange
        fieldUtRange = (field.obsTimes["start"], field.obsTimes["end"])
        fullVisRange = (field.obsTimes["start"] + datetime.timedelta(hours=-0.5),
                        field.obsTimes["end"] + datetime.timedelta(hours=0.5))
        # print(field.fieldID, "\n", fieldUtRange)
        fieldRow = VizRow(field, self.getTableDict(field), self.timeScale, self.haScale, setCurrent=self.setCurrent, isChild=self.isChild)
        fieldRow.addVizWindow( # draw on a white background
            name = "background",
            utRange = self.timeScale.range,
            haRange = self.haScale.range
        )
        fieldRow.addVizWindow( # background bar
            name = self.surveyName,
            utRange = self.timeScale.range,
            haRange = self.haScale.range
        )
        fieldRow.addVizWindow( # viz window
            name = "vizwindow",
            utRange = fullVisRange,
            haRange = fieldHaRange,
            primary = False  # probably?
        )
        fieldRow.addVizWindow( # viz window
            name = "zWarn1",
            utRange = fieldUtRange,
            haRange = fieldHaRange,
            primary = True
        )
        
        
        # # use 10 and 3 degree limits
        # if plate.haRange5DegZenith: # 85 degree warning
        #     plateRow.addVizWindow(
        #         name = "zWarn1",
        #         utRange = plate.utRange5DegZenith,
        #         haRange = plate.haRange5DegZenith,
        #     )
        # if plate.haRange3DegZenith: # 87 degree warning
        #     plateRow.addVizWindow(
        #         name = "zWarn2",
        #         utRange = plate.utRange3DegZenith,
        #         haRange = plate.haRange3DegZenith,
        #     )
        return fieldRow


class ApogeeViz(Viz):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, surveyName="apogee", **kwargs)


class childViz(Viz):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, surveyName="grey", isChild=True, **kwargs)


class FieldViz(VizRow):
    def __init__(self, schedule, field):
        """inputs:
        schedule: output from Autoscheduler.getSchedulerObsDict()
        field: a dbWrappers.field object
        """
        self.field = field
        self.timeScale = TimeScale((schedule["timeBarStartUTC"], schedule["timeBarEndUTC"]))
        self.haScale = Viz.haScale
        self.currentTime, self.currentHA = None, None
        self.setCurrent = True
        self.setCurrentMarkers()
        self.vizWindows = []
        self._basicFieldRow(field)


    def export(self):
        return {
            "vizWindows": [vizWindow.export() for vizWindow in self.vizWindows],
            "currentTime": datetime2dict(self.currentTime),
            "currentHA": self.currentHA, # used for current HA marker (may be None)
            "trueHA": self.field.haNow, # used for real time altitude display in Petunia (may not be None)
            "dec": self.field.dec,
            "isDone": False,   # self.plate.isComplete(),
            "timeScale": self.timeScale.export(),
            # "altitudePoints": self.getPlateAltitudePoints(),
            # "altitudePath": self.getPlateAltitudePoints(dense=True)
        }

    def _basicFieldRow(self, field):
        """field: scheduler.field instance
        """

        fieldHaRange = field.haRange
        fieldUtRange = (field.obsTimes["start"], field.obsTimes["end"])
        self.addVizWindow( # draw on a white background
            name = "background",
            utRange = self.timeScale.range,
            haRange = self.haScale.range
        )
        self.addVizWindow( # background bar
            name = "grey",
            utRange = self.timeScale.range,
            haRange = self.haScale.range
        )
        self.addVizWindow( # viz window
            name = "apogee",
            utRange = fieldUtRange,
            haRange = fieldHaRange
        )

        # # use 10 and 3 degree limits
        # if plate.haRange5DegZenith: # 85 degree warning
        #     self.addVizWindow(
        #         name = "zWarn1",
        #         utRange = plate.utRange5DegZenith,
        #         haRange = plate.haRange5DegZenith,
        #     )
        # if plate.haRange3DegZenith: # 87 degree warning
        #     self.addVizWindow(
        #         name = "zWarn2",
        #         utRange = plate.utRange3DegZenith,
        #         haRange = plate.haRange3DegZenith,
        #     )