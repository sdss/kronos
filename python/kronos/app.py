#!/usr/bin/env/python

import sys
from logging import getLogger, ERROR

import psycopg2
from quart import render_template, jsonify, request

# custom imports to suppress logging
from hypercorn.config import Config as HyperConfig
from hypercorn.asyncio import serve
from quart import Quart as _Quart

# this hack quiets logs a bit in theory
class Quart(_Quart):
    def run_task(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        debug=None,
        ca_certs=None,
        certfile=None,
        keyfile=None,
        shutdown_trigger=None
    ):
        config = HyperConfig()
        config.access_log_format = "%(r)s %(s)s %(b)s %(D)s"
        config.accesslog = logger
        config.bind = [f"{host}:{port}"]
        config.errorlog = config.accesslog

        return serve(self, config, shutdown_trigger=None)

if sys.version_info.minor > 9:
    # only works in 3.10+? just hacks at this point...
    app = Quart(__name__)
else:
    app = _Quart(__name__)

logger = getLogger('quart.serving')
logger.setLevel(ERROR)

print("{0}App '{1}' created.{2}".format('\033[92m', __name__, '\033[0m')) # to remove later

app.jinja_env.globals.update(zip=zip)

# Change the implementation of "decimal" to a C-based version (much! faster)
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except ImportError:
    pass  # no available

# -----------------------------------------------------------------------------
# The JSON module is unable to serialize Decimal objects, which is a problem
# as psycopg2 returns Decimal objects for numbers. This block of code overrides
# how psycopg2 parses decimal data types coming from the database, using
# the "float" data type instead of Decimal. This must be done separately for
# array data types.
#
# See link for other data types: http://initd.org/psycopg/docs/extensions.html
# -----------------------------------------------------------------------------
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)

# the decimal array is returned as a string in the form:
# "{1,2,3,4}"
DECARRAY2FLOATARRAY = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMALARRAY.values,
    'DECARRAY2FLOATARRAY',
    lambda value, curs: [float(x) if x else None for x in value[1:-1].split(",")] if value else None)
#    lambda value, curs: sys.stdout.write(value))
psycopg2.extensions.register_type(DECARRAY2FLOATARRAY)
# -----------------------------------------------------------------------------

# -------------------
# Register blueprints
# -------------------
from kronos.controllers.index import index_page
from kronos.controllers.fieldDetail import fieldDetail_page
from kronos.controllers.designDetail import designDetail_page
from kronos.controllers.planObserving import planObserving_page
from kronos.controllers.lookAhead import lookAhead_page
from kronos.controllers.fieldQuery import fieldQuery_page
from kronos.controllers.designQuery import designQuery_page
from kronos.controllers.mjdSummary import mjdSummary_page
from kronos.controllers.fieldViz import fieldViz_page
from kronos.controllers.dbEndPoints import dbEndPoints
from kronos.controllers.alterQueue import alterQueue_page
from kronos.controllers.timeTracking import timeTracking_page


from kronos.controllers import getTemplateDictBase

app.register_blueprint(index_page)
app.register_blueprint(fieldDetail_page)
app.register_blueprint(designDetail_page)
app.register_blueprint(planObserving_page)
app.register_blueprint(lookAhead_page)
app.register_blueprint(fieldQuery_page)
app.register_blueprint(designQuery_page)
app.register_blueprint(mjdSummary_page)
app.register_blueprint(fieldViz_page)
app.register_blueprint(dbEndPoints)
app.register_blueprint(alterQueue_page)
app.register_blueprint(timeTracking_page)

@app.errorhandler(404)
async def page_not_found(e):
    return await render_template('404.html', **getTemplateDictBase()), 404


@app.errorhandler(500)
async def err_page(e):
    """ Err page. """
    return await render_template("500.html", **getTemplateDictBase())
