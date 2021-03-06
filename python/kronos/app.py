#!/usr/bin/env/python

import os
import sys
import socket
from inspect import getmembers, isfunction

import psycopg2
from quart import Quart, render_template

from kronos import jinja_filters

# -----------------------------------------
# The snippet below is to hide the warning:
# /usr/local/python/lib/python2.7/site-packages/sqlalchemy/engine/reflection.py:40: SAWarning: Skipped unsupported reflection of expression-based index q3c_spectrum_idx
# WARNING: SAWarning: Skipped unsupported reflection of expression-based index q3c_psc_idx [sqlalchemy.util.langhelpers]
# -----------------------------------------
import warnings
warnings.filterwarnings(action="ignore", message="Skipped unsupported reflection")
warnings.filterwarnings(action="ignore", message='Predicate of partial index')
# -----------------------------------------

app = Quart(__name__)

print("{0}App '{1}' created.{2}".format('\033[92m', __name__, '\033[0m')) # to remove later

# Define custom filters into the Jinja2 environment.
# Any filters defined in the jinja_env submodule are made available.
# See: http://stackoverflow.com/questions/12288454/how-to-import-custom-jinja2-filters-from-another-file-and-using-flask
custom_filters = {name: function
                  for name, function in getmembers(jinja_filters)
                  if isfunction(function)}
app.jinja_env.filters.update(custom_filters)


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
from kronos.controllers.planObserving import planObserving_page
from kronos.controllers import getTemplateDictBase

app.register_blueprint(index_page)
app.register_blueprint(fieldDetail_page)
app.register_blueprint(planObserving_page)


@app.errorhandler(500)
async def err_page(e):
    """ Err page. """
    return await render_template("500.html", **getTemplateDictBase())
