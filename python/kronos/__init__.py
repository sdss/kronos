# encoding: utf-8
import os
import asyncio
from functools import partial

__version__ = "1.1.0"
rs_version = os.getenv("RS_VERSION")

observatory = os.getenv("OBSERVATORY")


async def wrapBlocking(func, *args, **kwargs):
    loop = asyncio.get_event_loop()

    wrapped = partial(func, *args, **kwargs)

    return await loop.run_in_executor(None, wrapped)
