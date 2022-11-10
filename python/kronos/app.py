#!/usr/bin/env/python

import sys
from inspect import getmembers, isfunction
from logging import getLogger, ERROR, FileHandler, DEBUG, Formatter

import psycopg2
from quart import Quart, render_template, jsonify, request

from kronos import jinja_filters

getLogger('quart.serving').setLevel(ERROR)

logger = getLogger('quart.app')
logger.setLevel(DEBUG)
# create file handler which logs even debug messages
fh = FileHandler('/data/logs/kronos/current.log')
fh.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

app = Quart(__name__)

print("{0}App '{1}' created.{2}".format('\033[92m', __name__, '\033[0m')) # to remove later

# Define custom filters into the Jinja2 environment.
# Any filters defined in the jinja_env submodule are made available.
# See: http://stackoverflow.com/questions/12288454/how-to-import-custom-jinja2-filters-from-another-file-and-using-flask
custom_filters = {name: function
                  for name, function in getmembers(jinja_filters)
                  if isfunction(function)}
app.jinja_env.filters.update(custom_filters)
app.jinja_env.globals.update(zip=zip)


# Change the implementation of "decimal" to a C-based version (much! faster)
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except ImportError:
    pass # no available

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


@app.errorhandler(404)
async def page_not_found(e):
    return await render_template('404.html', **getTemplateDictBase()), 404


@app.errorhandler(500)
async def err_page(e):
    """ Err page. """
    return await render_template("500.html", **getTemplateDictBase())
