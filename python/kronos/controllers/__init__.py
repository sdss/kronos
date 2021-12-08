#!/usr/bin/python
from subprocess import check_output
import re
import os

from quart import current_app

from kronos import observatory, __version__
from sdssdb import __version__ as dbVer
from roboscheduler import __version__ as rsVer


def getTemplateDictBase():
    version = __version__
    try:
        os.getlogin()
        isDev = True
    except OSError:
        # when run as a daemon, getlogin will fail
        isDev = False
    return {
        "isStable": False,
        "isDev": isDev,
        "observatory": observatory,
        "version": version,
        "RS_version": rsVer,
        "sdssdb_version": dbVer
    }
