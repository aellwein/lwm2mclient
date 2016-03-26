# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2016 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

# Implement your handlers here.

import asyncio
import logging
import time

logger = logging.getLogger("handlers")


def handle_firmware_update(*args, **kwargs):
    logger.info("handle_firmware_update(): {}, {}".format(args, kwargs))


def handle_disable(*args, **kwargs):
    logger.info("handle_disable(): {}, {}".format(args, kwargs))


def handle_update_trigger(*args, **kwargs):
    logger.info("handle_update_trigger(): {}, {}".format(args, kwargs))


def handle_reboot(*args, **kwargs):
    logger.info("handle_reboot(): {}, {}".format(args, kwargs))


def handle_factory_reset(*args, **kwargs):
    logger.info("handle_factory_reset(): {}, {}".format(args, kwargs))


def handle_reset_error_code(*args, **kwargs):
    logger.info("handle_reset_error_code(): {}, {}".format(args, kwargs))
    model = kwargs["model"]
    # reset error code in model data
    model.set_resource("3", "0", "11", {"0": 0})


cancel_observe_3_0_13 = False


@asyncio.coroutine
def do_notify(model, notifier):
    logger.info("do_notify(): {}".format(model, notifier))
    if cancel_observe_3_0_13:
        return
    # sleep 10 seconds asynchronously
    yield from asyncio.sleep(10)
    # change timestamp to current in client model
    model.set_resource("3", "0", "13", int(time.time()))
    # send a notification to server, if no cancel
    if not cancel_observe_3_0_13:
        notifier()
    # reschedule itself
    if not cancel_observe_3_0_13:
        asyncio.ensure_future(do_notify(model, notifier))


def observe_3_0_13(*args, **kwargs):
    global cancel_observe_3_0_13
    logger.info("observe_3_0_13(): {}, {}".format(args, kwargs))
    model = kwargs["model"]
    notifier = kwargs["notifier"]
    cancel_observe_3_0_13 = kwargs["cancel"]
    asyncio.ensure_future(do_notify(model, notifier))
