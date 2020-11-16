#!/usr/bin/env/python

from quart import render_template, Blueprint

from . import getTemplateDictBase


index_page = Blueprint("index_page", __name__)


@index_page.route('/', methods=['GET'])
async def index():
    """ Index page. """
    return await render_template("index.html", **getTemplateDictBase())
