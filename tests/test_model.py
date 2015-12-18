#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import json

import pytest

from model import ClientModel, DefinitionFileLoader, DataFileLoader


@pytest.fixture
def empty_data_loader():
    class Loader(object):
        def __init__(self):
            pass

        def load(self):
            return json.loads("{}")

    return Loader()


@pytest.fixture
def empty_definition_loader():
    class Loader(object):
        def __init__(self):
            pass

        def load(self):
            return json.loads("{}")

    return Loader()


@pytest.fixture
def model(definition_loader=DefinitionFileLoader(), data_loader=DataFileLoader()):
    return ClientModel(definition_loader=definition_loader, data_loader=data_loader)


def test_invalid_definition_loader():
    with pytest.raises(AttributeError):
        ClientModel(definition_loader=1)


def test_invalid_data_loader():
    with pytest.raises(AttributeError):
        ClientModel(data_loader=1)


def test_non_existing_definition_file_raises_error():
    with pytest.raises(FileNotFoundError):
        ClientModel(definition_loader=DefinitionFileLoader(definition_file="nonexisting.json"))


def test_non_existing_data_file_raises_error():
    with pytest.raises(FileNotFoundError):
        ClientModel(data_loader=DataFileLoader(data_file="nonexisting.json"))


def test_use_undefined_object(empty_definition_loader):
    with pytest.raises(AttributeError):
        ClientModel(definition_loader=empty_definition_loader)


def test_objects(empty_data_loader):
    model = ClientModel(data_loader=empty_data_loader)
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


def test_path_with_invalid_object(model):
    with pytest.raises(KeyError):
        assert model.resource(999999, 0, 0)


def test_path_with_invalid_instance(model):
    with pytest.raises(KeyError):
        assert model.resource(3, 1, 0)


def test_path_with_invalid_resource(model):
    with pytest.raises(KeyError):
        assert model.resource(3, 0, 99999)


def test_is_object_multi_instance(model):
    assert model.is_object_multi_instance(1), "server object is a multi-instance object"
    assert model.is_object_multi_instance(3) is False, "device object is a single-instance object"


def test_is_resource_multi_instance(model):
    assert model.is_resource_multi_instance(3, 0, 11), "must be a multi-instance resource"
    assert model.is_resource_multi_instance(3, 0, 0) is False, "must be a single-instance resource"


def test_is_resource_readable(model):
    assert model.is_resource_readable(3, 0, 0), "must be readable"
    assert model.is_resource_readable(1, 0, 1), "must be readable"
    assert model.is_resource_readable(0, 0, 0) is False, "must not be readable"
    assert model.is_resource_readable(3, 0, 4) is False, "must not be readable"


def test_is_resource_writable(model):
    assert model.is_resource_writable(3, 0, 13), "must be writable"
    assert model.is_resource_writable(5, 0, 0), "must be writable"
    assert model.is_resource_writable(0, 0, 0) is False, "must not be writable"
    assert model.is_resource_writable(3, 0, 4) is False, "must not be writable"


def test_is_resource_executable(model):
    assert model.is_resource_executable(3, 0, 4), "must be executable"
    assert model.is_resource_executable(0, 0, 0) is False, "must not be executable"
    assert model.is_resource_executable(3, 0, 0) is False, "must not be executable"


def test_instance_iter(model):
    instances = list(model.instance_iter())
    for obj in model.objects():
        for instance in model.instances(obj):
            assert (str(obj), str(instance)) in instances


def test_resource_iter(model):
    resources = list(model.resource_iter())
    for obj in model.objects():
        for inst in model.instances(obj):
            for res in model.resources(obj, inst):
                assert (str(obj), str(inst), str(res)) in resources


def test_get_object_links(model):
    obj_links = ",".join(model.get_object_links())
    for obj in model.objects():
        for inst in model.instances(obj):
            assert "</%s/%s>" % (obj, inst) in obj_links


def test_set_resource_on_read_only(model):
    r = model.resource(3, 0, 0)
    model.set_resource(3, 0, 0, "blah")
    assert r == model.resource(3, 0, 0), "resource /3/0/0 must not be changed"


def test_set_resource(model):
    r = model.resource(3, 0, 14)
    new_value = "+1" if r == "+2" else "+2"
    model.set_resource(3, 0, 14, new_value)
    assert new_value == model.resource(3, 0, 14), "resource /3/0/14 must be changed"


def test_apply(model):
    r = model.resource(3, 0, 14)
    new_value = "+1" if r == "+2" else "+2"
    change = {"3": {"0": {"14": new_value}}}
    model.apply(change)
    assert new_value == model.resource(3, 0, 14), "resource /3/0/14 must be changed"
