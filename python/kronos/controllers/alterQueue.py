# -*- coding: utf-8 -*-
from quart import request, render_template, Blueprint

from astropy.time import Time
import numpy as np

from sdssdb.peewee.sdss5db import opsdb

from kronos import wrapBlocking
from kronos.scheduler import Queue

from . import getTemplateDictBase

alterQueue_page = Blueprint("alterQueue_page", __name__)


def moveDesigns(positions, designs):
    Q = opsdb.Queue
    for p, d in zip(positions, designs):
        pos = Q.get(position=p)
        pos.design_id = d
        pos.save()


@alterQueue_page.route('/alterQueue.html', methods=['GET', 'POST'])
async def alterQueue():
    form = await request.form

    errors = list()

    field_pk = None

    if "field_pk" in form:
        # expect direction to be positive or negative integer
        field_pk = int(form["field_pk"])
        direction = int(form["direction"])

        up = direction > 0

        queue = await wrapBlocking(Queue)
        pks = [d.field_pk for d in queue.designs if d.position > 0]
        field_ids = np.array([d.fieldID for d in queue.designs if d.position > 0])
        design_ids = np.array([d.designID for d in queue.designs if d.position > 0])

        to_move = np.where([p == field_pk for p in pks])

        move_id = field_ids[to_move][0]

        if 0 in to_move[0] and up:
            errors.append(f"cannot move {move_id} up, already first")
        elif len(pks) - 1 in to_move[0] and not up:
            errors.append(f"cannot move {move_id} down, already already last")

    if len(errors) == 0 and field_pk is not None:
        if up:
            replace_field = pks[np.min(to_move[0]) - 1]
        else:
            replace_field = pks[np.max(to_move[0]) + 1]

        replace_pos = np.where([p == replace_field for p in pks])
        move_by = len(replace_pos[0])

        if up:
            n_moving = len(to_move[0])
            # +1 since we've successfully 0-indexed here but queue starts at 1
            upPos = [pos - move_by + 1 for pos in to_move[0]]
            upDesigns = design_ids[to_move]
            await wrapBlocking(moveDesigns, upPos, upDesigns)
            downPos = [pos + n_moving + 1 for pos in replace_pos[0]]
            downDesigns = design_ids[replace_pos]
            await wrapBlocking(moveDesigns, downPos, downDesigns)
        else:
            n_moving = len(to_move[0])
            upPos = [pos + move_by + 1 for pos in to_move[0]]
            upDesigns = design_ids[to_move]
            await wrapBlocking(moveDesigns, upPos, upDesigns)
            downPos = [pos - n_moving + 1 for pos in replace_pos[0]]
            downDesigns = design_ids[replace_pos]
            await wrapBlocking(moveDesigns, downPos, downDesigns)

    templateDict = getTemplateDictBase()

    # startTime = Time(mjd_evening_twilight, format="mjd").datetime
    # endTime = Time(mjd_morning_twilight, format="mjd").datetime

    queue = await wrapBlocking(Queue)

    last_pk = 0
    color = "cyan"
    next_color = "LightSteelBlue"
    for d in queue.designs:
        d.priority = queue.fieldDict[d.field_pk].priority
        if d.field_pk != last_pk:
            last_pk = d.field_pk
            old_color = color
            color = next_color
            next_color = old_color
        d.fieldColor = color

    templateDict.update({
        "queue": queue.designs,
        "errorMsg": errors
    })

    # findAndConvertDatetimes(templateDict)
    return await render_template("alterQueue.html", **templateDict)


if __name__ == "__main__":
    pass
