#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import pytest
from model import ClientModel


@pytest.fixture
def empty_data(tmpdir):
    json = "{}"
    fname = os.path.join(tmpdir.strpath, "emptydata.json")
    with open(fname, "w") as f:
        f.writelines(json)
        return fname


@pytest.fixture
def empty_definition(tmpdir):
    json = "{}"
    fname = os.path.join(tmpdir.strpath, "emptydefinition.json")
    with open(fname, "w") as f:
        f.writelines(json)
        return fname


@pytest.fixture
def some_data(tmpdir):
    json = "{ \"0\" : {} }"
    fname = os.path.join(tmpdir.strpath, "somedata.json")
    with open(fname, "w") as f:
        f.writelines(json)
        return fname


@pytest.fixture
def model():
    return ClientModel()


def test_invalid_definition_file():
    with pytest.raises(AssertionError):
        ClientModel(definition_file=1)


def test_invalid_data_file():
    with pytest.raises(AssertionError):
        ClientModel(data_file=1.0)


def test_non_existing_definition_file_raises_error():
    with pytest.raises(FileNotFoundError):
        ClientModel(definition_file="nonexisting.json")


def test_non_existing_data_file_raises_error():
    with pytest.raises(FileNotFoundError):
        ClientModel(data_file="nonexisting.json")


def test_use_undefined_object(empty_definition, some_data):
    with pytest.raises(AttributeError):
        ClientModel(definition_file=empty_definition, data_file=some_data)


def test_objects(empty_data):
    model = ClientModel(data_file=empty_data)
    assert len(model.objects()) == 0, "should be empty"


def test_apply_with_invalid_parameter(model):
    with pytest.raises(AssertionError):
        model.apply(1)


def test_path_with_wrong_length(model):
    with pytest.raises(AttributeError):
        model.is_path_valid((1, 2, 3, 4,))


def test_path_with_invalid_elements(model):
    with pytest.raises(AssertionError):
        assert model.is_path_valid(('a', 3,))


def test_path_object_id_is_valid(model):
    assert model.is_path_valid((3,)), "path for objectID must be valid."


def test_path_object_id_and_instance_id_is_valid(model):
    assert model.is_path_valid((3, 0,)), "path for objectID with instanceID must be valid."


def test_path_object_id_instance_id_and_resource_id_is_valid(model):
    assert model.is_path_valid((3, 0, 1)), "path for objectID with instanceID must be valid."
