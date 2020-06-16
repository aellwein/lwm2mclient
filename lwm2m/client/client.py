import asyncio
import importlib
import logging
import sys
from argparse import ArgumentParser
from os.path import join

import aiocoap
from aiocoap import resource

from lwm2m.client.defaults import Defaults
from lwm2m.client.logger import levels, logger, text_to_level
from lwm2m.client.model import ModelLoader


class Client:
    server_host = Defaults.SERVER_HOST.value
    server_port = Defaults.SERVER_PORT.value
    client_host = Defaults.CLIENT_HOST.value
    client_port = Defaults.CLIENT_PORT.value
    model_loader = Defaults.MODEL_LOADER.value
    model_path = Defaults.MODEL_PATH.value
    model = None
    site = aiocoap.resource.Site()

    def __init__(self, **args):
        for i in args.keys():
            setattr(self, i, args[i])

        self.ml = self._get_model_loader()
        logger.info(f'Using model loader: {self.ml}')
        self.model = self.ml.load_model(self.model_path)

    def _get_model_loader(self):
        _ml = self.model_loader.rsplit(':', 1)
        if len(_ml) != 2:
            raise AttributeError(
                'model loader must be in form of: package.subpackage.module:ClassName')
        ml_path, ml_class_name = _ml[0], _ml[1]
        ml_module = importlib.import_module(ml_path)
        cls = getattr(ml_module, ml_class_name)
        if not issubclass(cls, ModelLoader):
            raise AttributeError(
                f'{self.model_loader} is not a subclass of lwm2m.client.model.ModelLoader')
        ml_instance = cls()
        return ml_instance

    async def main(self):
        """
        Entrypoint for use with ``asyncio.run()``.
        """
        if self.model is None:
            raise AttributeError(
                'Model attribute has to be provided (as a class name)')


def get_args():
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
        '--client-host',
        type=str,
        default=Defaults.CLIENT_HOST.value,
        help=f'Host (interface) for client to listen on (default: {Defaults.CLIENT_HOST.value})'
    )
    parser.add_argument(
        '--client-port',
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
        '--model-loader',
        type=str,
        default=Defaults.MODEL_LOADER.value,
        help=f'Model loader class to be used (default: "{Defaults.MODEL_LOADER.value}")'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default=Defaults.MODEL_PATH.value,
        help=f'Path to directory where to look for model files (default: "{Defaults.MODEL_PATH.value}")'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Shortcut for "--loglevel DEBUG"'
    )

    args = parser.parse_args()

    args.loglevel = logging.DEBUG if args.debug else text_to_level(
        args.loglevel) if args.loglevel else logging.WARN

    logging.basicConfig(
        level=args.loglevel,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    eargs = dict(**vars(args))
    logger.debug(f'Effective args: {eargs}')
    return eargs


def main(args=None):
    _args = args if args is not None else get_args()
    asyncio.run(Client(**_args).main())
