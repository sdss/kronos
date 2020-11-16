#!/usr/bin/python

"""
This file contains all custom Jinja2 filters.
"""


def j2PlugStatusSelectable(status):
    """From a plugging status, determine if this
    selectable (basically only statuses with Overridden)
    """
    if "overrid" in status.lower() or "special" in status.lower() or "test" in status.lower():
        return True
    else:
        return False


def j2HasProfilometries(platePluggings):
    """Return true if a plate has profilometry measurements
    @param[in] platePluggings, list of plate plugging dictionaries (as returned by utils.getPluggingDict)
    """
    profs = [len(x.profilometries) for x in platePluggings]
    return sum(profs) > 0


def j2bgColorFromMeas(meas, tolerance):
    """Return a color based on whether or not meas is within the profilometry tolerance range
    """
    if meas is None:
        return ""
    if str(meas) in ["NaN", "nan"] or str(meas) == "Err":
        return "danger"
    if abs(float(meas)) > float(tolerance[0]):
        bgColor = "danger"
    elif abs(float(meas)) < float(tolerance[1]):
        bgColor = "info"
    else:
        bgColor = "success"
    return bgColor


def j2FmtProfValue(value):
    if value is None:
        return ""
    try:
        return abs(float(value))
    except:
        return value


def j2isValidSurveyMode(mode, plate):
    if plate.isBoss and "boss" in mode.lower():
        return True
    if plate.isManga and "ma" in mode.lower():
        return True
    if plate.isApogee and "apogee" in mode.lower():
        return True
    return False


def j2getCart(plate):
    """If autoscheduled cart is present return that, else return current
    cart, or None if the plate is not plugged
    """
    if plate.assignedCart is not None:
        return plate.assignedCart
    else:
        return plate.cartNumber  # may be None


def j2sortByAttr(aList, attrOnList, reverse=0):
    reverse = bool(reverse)
    return sorted(aList, key=lambda listElement: getattr(listElement, attrOnList), reverse=reverse)


def j2plugTextBold(textLine):
    if "eBOSS Autoscheduler Not Yet Implemented" in textLine:
        return False
    if textLine.strip().endswith("SAME"):
        return False
    if textLine.strip().endswith("...."):
        return False
    return True
