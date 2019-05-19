# Implement your handlers here.

import asyncio
import logging
import time

log = logging.getLogger('handlers')


def handle_firmware_update(*args, **kwargs):
    log.info(f'handle_firmware_update(): {args}, {kwargs}')


def handle_disable(*args, **kwargs):
    log.info(f'handle_disable(): {args}, {kwargs}')


def handle_update_trigger(*args, **kwargs):
    log.info(f'handle_update_trigger(): {args}, {kwargs}')


def handle_reboot(*args, **kwargs):
    log.info(f'handle_reboot(): {args}, {kwargs}')


def handle_factory_reset(*args, **kwargs):
    log.info(f'handle_factory_reset(): {args}, {kwargs}')


def handle_reset_error_code(*args, **kwargs):
    log.info(f'handle_reset_error_code(): {args}, {kwargs}')
    model = kwargs['model']
    # reset error code in model data
    model.set_resource('3', '0', '11', {'0': 0})


cancel_observe_3_0_13 = False


async def do_notify(model, notifier):
    log.info(f'do_notify(): {model}, {notifier}')
    if cancel_observe_3_0_13:
        return
    # sleep 10 seconds asynchronously
    await asyncio.sleep(10)
    # change timestamp to current in client model
    model.set_resource('3', '0', '13', int(time.time()))
    # send a notification to server, if no cancel
    if not cancel_observe_3_0_13:
        notifier()
    # reschedule itself
    if not cancel_observe_3_0_13:
        asyncio.ensure_future(do_notify(model, notifier))


def observe_3_0_13(*args, **kwargs):
    global cancel_observe_3_0_13
    log.info(f'observe_3_0_13(): {args}, {kwargs}')
    model = kwargs['model']
    notifier = kwargs['notifier']
    cancel_observe_3_0_13 = kwargs['cancel']
    asyncio.ensure_future(do_notify(model, notifier))
