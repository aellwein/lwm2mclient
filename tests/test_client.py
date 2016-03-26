#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2016 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.
import pytest

from client import *


@pytest.fixture
def model():
    return ClientModel()


@pytest.fixture
def client(model):
    return Client(model)


def test_resource_handlers_are_created(client, model):
    assert client.model == model
    resources = list(model.resource_iter())
    for res in resources:
        assert res in client._resources
    instances = list(model.instance_iter())
    for inst in instances:
        assert inst in client._resources
