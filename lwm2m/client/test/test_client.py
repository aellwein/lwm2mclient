import sys

import pytest

from lwm2m.client import client
from lwm2m.client.model import ModelLoader


def test_get_args(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--server-host', 'someip'])
    a = client.get_args()
    assert 'server_host' in a and a['server_host'] == 'someip'


def test_get_args_with_invalid_args(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--some-option', 'garbage'])
    with pytest.raises(SystemExit):
        client.get_args()


def test_invalid_model_loader_spec(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--model-loader', 'not.existing', '--debug'])
    with pytest.raises(AttributeError):
        client.Client(**client.get_args())


def test_non_existing_model_loader_package(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--model-loader', 'not.existing:SomeClass', '--debug'])
    with pytest.raises(ModuleNotFoundError):
        client.Client(**client.get_args())


def test_non_existing_model_loader_class(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--model-loader', 'lwm2m.client.model:NonExistingModelLoader', '--debug'])
    with pytest.raises(AttributeError):
        client.Client(**client.get_args())


class InvalidModelLoader:
    def load_model(self, path):
        pass


class ValidModelLoaderBadInitSignature(ModelLoader):
    def __init__(self, aa):
        pass

    def load_model(self, path):
        return {}


class ValidModelLoader(ModelLoader):
    def __init__(self):
        pass

    def load_model(self, path):
        return {}


def test_wrong_model_loader_subclass(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--model-loader', 'lwm2m.client.test.test_client:InvalidModelLoader', '--debug'])
    with pytest.raises(AttributeError):
        client.Client(**client.get_args())


def test_model_loader_with_bad_constructor(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--model-loader', 'lwm2m.client.test.test_client:ValidModelLoaderBadInitSignature', '--debug'])
    with pytest.raises(TypeError):
        client.Client(**client.get_args())


def test_valid_model_loader_subclass(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', [sys.argv[0], '--model-loader', 'lwm2m.client.test.test_client:ValidModelLoader', '--debug'])
    client.Client(**client.get_args())
