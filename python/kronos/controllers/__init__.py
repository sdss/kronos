#!/usr/bin/python
from subprocess import check_output
import re
import os

from quart import current_app

from kronos import observatory

# comple pattern for matching revision
revPattern = re.compile(r"^Revision: (?P<revisionNum>\d+)$", re.MULTILINE)

def getVersion(path):
    """Input:
    path, a string representing an absolute path to a current version of software
    """
    realPath = os.path.realpath(path)
    baseDir = realPath.split("/")[-1]
    #see if this path is an svn repo, if so get version number
    try:
        stdoutStr = check_output(["svn", "info", realPath])
        revisionNum = re.search(revPattern, stdoutStr).groupdict()["revisionNum"]
    except:
        # not an svn repo
        return baseDir
    else:
        return baseDir + " r%s"%revisionNum


def getTemplateDictBase():
    # isStable = current_app.config["AS_PORT"]=="8091"
    # isDev = current_app.config["DB_PORT"]=="5440"
    version = "current"
    return {
        "isStable": False,
        "isDev": True,
        "observatory": observatory
    }
