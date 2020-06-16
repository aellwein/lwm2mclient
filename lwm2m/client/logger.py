import logging

logger = logging.getLogger('lwm2mclient')

levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'WARNING': logging.WARN,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
    'CRITICAL': logging.CRITICAL
}


def text_to_level(lvl: str) -> int:
    if lvl not in levels:
        raise ValueError(f'FATAL: invalid logging level provided: {lvl}')

    return levels[lvl]
