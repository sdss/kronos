
.. _intro:

Introduction to Kronos
===============================

``Kronos`` is the user/observer interface for scheduling FPS observations in SDSS V. The goal for the Kronos webapp is to facilitate easy and efficient observation planning. Kronos uses the ``roboscheduler`` product to schedule observation and updates the observing queue.

The Observing Queue
-------------------

Scheduling centers around a "queue" of designs to be observed. The queue is a table in opsDB which will provide SOP with the next design to configure on the FPS via the popQueue database function. The queue is only populated and modified in ``Kronos``. 

Individual entries in the queue are designs, meaning a field with multiple exposures (e.g. an RM field) will have multiple entries in the queue. In normal operations, designs will be "popped" off the queue one at a time. In order to respect cadence requirements, this is the only time individual designs can be removed from the queue. Within ``Kronos``, only entire fields can be removed. If a field is in the middle of an epoch (e.g. if weather interrupts a sequence of observations), ``Kronos`` will receive the appropriate designs to complete the epoch from the scheduler add them to the queue.
