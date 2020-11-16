from flask import current_app
import datetime

def debugMsg(aMsg):
    current_app.logger.debug(aMsg)
    print(str(datetime.datetime.now()), aMsg)

def logMsg(aMsg):
    current_app.logger.info(aMsg)
    print(str(datetime.datetime.now()), aMsg)

def errMsg(aMsg):
    current_app.logger.error(aMsg)
    print(str(datetime.datetime.now()), "Error: ", aMsg)