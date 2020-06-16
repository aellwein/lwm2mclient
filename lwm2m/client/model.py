import logging
import os
from abc import ABCMeta, abstractclassmethod, abstractmethod
from os.path import exists, join

from yaml import dump, load

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


logger = logging.getLogger('model')


class ModelLoader(metaclass=ABCMeta):
    @abstractmethod
    def load_model(self, path):
        raise NotImplementedError(
            'this method has to be implemented by the subclass')

    def __repr__(self):
        return '.'.join([self.__class__.__module__, self.__class__.__name__])


class YamlModelLoader(ModelLoader):
    def load_model(self, path):
        path_file = os.path.join(path, 'model.yml')
        if not os.path.exists(path_file):
            raise IOError(
                f'unable to locate model file "{path_file}" at expected location.')
        logger.debug(f'Loading model from "{path_file}"...')
        with open(path_file, 'r') as model_file:
            data = load(model_file, Loader=Loader)
        logger.debug(f'Model loaded: {data}')
        return data
