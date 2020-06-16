import logging
from argparse import ArgumentParser
from os.path import join

from lwm2m.client.defaults import Defaults
from lwm2m.client.logger import levels, logger, text_to_level


class Client:
    pass


def main():
    parser = ArgumentParser('lwm2mclient')
    parser.add_argument(
        '--server-host',
        type=str,
        default=Defaults.SERVER_HOST.value,
        help=f'LWM2M server IP address to connect to (default: {Defaults.SERVER_HOST.value})'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=Defaults.SERVER_PORT.value,
        help=f'LWM2M server port to use (default: {Defaults.SERVER_PORT.value})'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=Defaults.CLIENT_HOST.value,
        help=f'Host (interface) for client to listen on (default: {Defaults.CLIENT_HOST.value})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=Defaults.CLIENT_PORT.value,
        help=f'Port for client to listen on (default: {Defaults.CLIENT_PORT.value})'
    )
    parser.add_argument(
        '--loglevel',
        type=str,
        default=Defaults.LOGLEVEL.value,
        help=f'Cap log level to use, one of {",".join(tuple(levels.keys()))}, default: {Defaults.LOGLEVEL.value}'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Shortcut for --loglevel DEBUG'
    )

    args = parser.parse_args()

    lvl = logging.DEBUG if args.debug else text_to_level(
        args.loglevel) if args.loglevel else logging.WARN

    logging.basicConfig(
        level=lvl,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.debug(f'Effective arguments: {vars(args)}')
