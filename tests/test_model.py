#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

from model import ClientModel


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


def test_apply_with_invalid_parameter():
    with pytest.raises(AssertionError):
        model = ClientModel()
        model.apply(1)
