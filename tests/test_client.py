#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
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


def test_bla(client, model):
    assert client.model == model
