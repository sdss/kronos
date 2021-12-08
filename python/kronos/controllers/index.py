#!/usr/bin/env/python

from quart import render_template, Blueprint

from kronos import wrapBlocking
from kronos.scheduler import Queue

from . import getTemplateDictBase


index_page = Blueprint("index_page", __name__)


@index_page.route('/', methods=['GET'])
async def index():
    """ Index page. """
    queue = await wrapBlocking(Queue)

    templateDict = getTemplateDictBase()

    templateDict.update({"queue": queue.designs})

    return await render_template("index.html", **templateDict)
