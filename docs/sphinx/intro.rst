
.. _intro:

Introduction to Kronos
===============================

``Kronos`` is the user/observer interface for scheduling FPS observations in SDSS V. The goal for the Kronos webapp is to facilitate easy and efficient observation planning. Kronos uses the ``roboscheduler`` product to schedule observation and updates the observing queue.

The Observing Queue
-------------------

Scheduling centers around a "queue" of designs to be observed. The queue is a table in opsDB which will provide SOP with the next design to configure on the FPS via the popQueue database function. The queue is only populated and modified in ``Kronos``. 

Individual entries in the queue are designs, meaning a field with multiple exposures (e.g. an RM field) will have multiple entries in the queue. In normal operations, designs will be "popped" off the queue one at a time. In order to respect cadence requirements, this is the only time individual designs can be removed from the queue. Within ``Kronos``, only entire fields can be removed. If a field is in the middle of an epoch (e.g. if weather interrupts a sequence of observations), ``Kronos`` will receive the appropriate designs to complete the epoch from the scheduler add them to the queue.


Developing
----------

``Kronos`` is based on the ``quart`` framework, which is an ``asyncio`` clone of the popular ``flask`` framework. See the `quart documenation <https://pgjones.gitlab.io/quart/index.html>`__ for more information.

To run ``Kronos`` locally, it is recommended to clone the latest version from github and pip install in editable mode. From the top level directory, this is done by ::

    pip install -e .

This installs ``Kronos`` and most dependenceies. But as of 0.1.0, ``sdssdb`` and ``roboscheduler`` are not installed automatically. While ``sdssdb`` is available on pypi and can be installed simply by ::

    pip install sdssdb

``roboscheduler`` is not. The install instructions for ``roboscheduler`` are somewhat more difficult as of writing, and that documentation should be referenced. Both ``roboscheduler`` and ``sdssdb`` are required for ``Kronos``.

``quart`` requires a ``$QUART_APP`` environment variable that in this case should point to ``/path/to/kronos/main/python/kronos/app:app``. The app can now be run with ::

    quart run

When setup in this way, the app will refresh any time any of the source code changes on disk.
