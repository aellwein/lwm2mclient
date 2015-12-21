#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.
import json

import pytest

from encdec import *
from model import ClientModel

logging.basicConfig(level=logging.CRITICAL)


@pytest.fixture
def model():
    return ClientModel()


@pytest.fixture
def payload_decoder(model):
    return PayloadDecoder(model)


@pytest.fixture
def payload_encoder(model):
    return PayloadEncoder(model)


@pytest.fixture
def special_definition():
    class DefLoader:
        def __init__(self):
            pass

        def load(self):
            _json = """
            {
                "1337": {
                    "name": "TEST OBJECT",
                    "id": 0,
                    "instancetype": "multiple",
                    "mandatory": true,
                    "description": "",
                    "resourcedefs": {
                        "0": {
                            "id": 0,
                            "name": "Test-Integer-Single",
                            "operations": "R",
                            "instancetype": "single",
                            "mandatory": false,
                            "type": "integer",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "1": {
                            "id": 1,
                            "name": "Test-Integer-Multi",
                            "operations": "R",
                            "instancetype": "multiple",
                            "mandatory": false,
                            "type": "integer",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "2": {
                            "id": 2,
                            "name": "Test-String-Single",
                            "operations": "R",
                            "instancetype": "single",
                            "mandatory": false,
                            "type": "string",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "3": {
                            "id": 3,
                            "name": "Test-String-Multi",
                            "operations": "R",
                            "instancetype": "multiple",
                            "mandatory": false,
                            "type": "string",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "4": {
                            "id": 4,
                            "name": "Test-Float-Single",
                            "operations": "R",
                            "instancetype": "single",
                            "mandatory": false,
                            "type": "float",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "5": {
                            "id": 5,
                            "name": "Test-Float-Multi",
                            "operations": "R",
                            "instancetype": "multiple",
                            "mandatory": false,
                            "type": "float",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "6": {
                            "id": 6,
                            "name": "Test-Boolean-Single",
                            "operations": "R",
                            "instancetype": "single",
                            "mandatory": false,
                            "type": "boolean",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "7": {
                            "id": 7,
                            "name": "Test-Boolean-Multi",
                            "operations": "R",
                            "instancetype": "multiple",
                            "mandatory": false,
                            "type": "boolean",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "8": {
                            "id": 8,
                            "name": "Test-Time-Single",
                            "operations": "R",
                            "instancetype": "single",
                            "mandatory": false,
                            "type": "time",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "9": {
                            "id": 9,
                            "name": "Test-Time-Multi",
                            "operations": "R",
                            "instancetype": "multiple",
                            "mandatory": false,
                            "type": "time",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "10": {
                            "id": 10,
                            "name": "Test-Opaque-Single",
                            "operations": "R",
                            "instancetype": "single",
                            "mandatory": false,
                            "type": "opaque",
                            "range": "",
                            "units": "",
                            "description": ""
                        },
                        "11": {
                            "id": 11,
                            "name": "Test-Opaque-Multi",
                            "operations": "R",
                            "instancetype": "multiple",
                            "mandatory": false,
                            "type": "opaque",
                            "range": "",
                            "units": "",
                            "description": ""
                        }
                    }
                }
            }"""
            return json.loads(_json)

    return DefLoader()


@pytest.fixture
def special_data():
    class DataLoader:
        def __init__(self):
            pass

        def load(self):
            return json.loads("""
                {
                    "1337": {
                        "0": {
                            "0": 1338,
                            "1": { "0": 1338, "1": 1339 },
                            "2": "python",
                            "3": { "0": "to", "1": "beer", "2": "or", "3": "not", "4": "to", "5": "beer" },
                            "4": 3.1415,
                            "5": { "0": 1.1, "1": -0.000003, "2": 6732.23 },
                            "6": true,
                            "7": { "0": true, "1": false, "2": false, "3": true },
                            "8": 387292,
                            "9": { "0": 362762, "1": 3404383322 },
                            "10": "cafebabe",
                            "11": { "0": "cafebabe", "1": "deadbeef" }
                        },
                        "1": {
                            "0": 8372,
                            "1": { "0": 32324, "1": -13323239 },
                            "2": "Typhoon",
                            "3": { "0": "take", "1": "me", "2": "to", "3": "your", "4": "leader" },
                            "4": 4332232.4387,
                            "5": { "0": -2321.1, "1": 2.3, "2": 6732.23 },
                            "6": true,
                            "7": { "0": true, "1": false, "2": false, "3": true },
                            "8": 323276674,
                            "9": { "0": 76543434, "1": 87543957 },
                            "10": "bada55",
                            "11": { "0": "c001d00d", "1": "deadc0de" }
                        }
                    }
                }""")

    return DataLoader()


def test_payload_with_invalid_path_type(payload_decoder):
    with pytest.raises(AssertionError):
        payload_decoder.decode(1, None, None)


def test_payload_decoder_checks_path(payload_decoder):
    message, path = payload_decoder.decode((3, 1, 0), None, None)
    assert message.code == Code.NOT_FOUND, "message code should be NOT FOUND"
    assert path is None


def test_payload_decoder_content_type_check(payload_decoder):
    with pytest.raises(ContentFormatException):
        payload_decoder.decode((3, 0, 0), None, None)


def test_payload_decoder_content_type_text(payload_decoder):
    message, apply = payload_decoder.decode((3, 0, 0), "blah".encode(), MediaType.TEXT.value)
    assert message.code == Code.CHANGED, "message code should be CHANGED"
    assert apply == {'3': {'0': {'0': 'blah'}}}


def test_payload_decoder_content_type_text_raises_on_object_path(payload_decoder):
    with pytest.raises(ContentFormatException):
        payload_decoder.decode((3,), "blah".encode(), MediaType.TEXT.value)


def test_payload_decoder_content_type_text_raises_on_instance_path(payload_decoder):
    with pytest.raises(ContentFormatException):
        payload_decoder.decode((3, 0,), "blah".encode(), MediaType.TEXT.value)


def test_payload_decoder_generates_bad_request_response(payload_decoder):
    message, apply = payload_decoder.decode((3, 0, 0,), b"\xde\xad\xbe\xaf", MediaType.TEXT.value)
    assert message.code == Code.BAD_REQUEST, "should be BAD REQUEST"
    assert apply is None


def test_payload_decoder_content_type_tlv_with_broken_payload(payload_decoder):
    message, apply = payload_decoder.decode((3, 0), b"\xde\xad", MediaType.TLV.value)
    assert message.code == Code.BAD_REQUEST, "should be BAD REQUEST"
    assert message.payload == "invalid resource path: /3/0/173".encode()
    assert apply is None


def test_payload_decoder_content_type_tlv_object(payload_decoder):
    payload = bytearray.fromhex(
            "C800154F70656E20536F7572636520436F6D6D756E697479C801114C574D324D20436C69656E742076302E31C70231323334353637C8030F4657303132362D33363335322E5631860641050541000088070842050CE442000CE4880808420500FA420000FAC10963C20A07EE830B410001C80D0800000000000BF3B7C20E2B32C80F0D4575726F70652F4265726C696EC2105551")
    message, apply = payload_decoder.decode((3,), payload, MediaType.TLV.value)
    assert message.code == Code.CHANGED
    assert len(apply["3"]["0"]) == 14


def test_payload_decoder_content_type_tlv_instance(payload_decoder):
    payload = bytearray.fromhex(
            "C800154F70656E20536F7572636520436F6D6D756E697479C801114C574D324D20436C69656E742076302E31C70231323334353637C8030F4657303132362D33363335322E5631860641050541000088070842050CE442000CE4880808420500FA420000FAC10963C20A07EE830B410001C80D0800000000000BF3B7C20E2B32C80F0D4575726F70652F4265726C696EC2105551")
    message, apply = payload_decoder.decode((3, 0,), payload, MediaType.TLV.value)
    assert message.code == Code.CHANGED
    assert len(apply["3"]["0"]) == 14


def test_payload_encoder_object(payload_encoder):
    message = payload_encoder.encode((3,))
    assert message.code == Code.CONTENT
    assert message.opt.content_format == MediaType.TLV.value
    assert len(message.payload) > 0


def test_payload_encoder_object_instance(payload_encoder):
    message = payload_encoder.encode((3, 0))
    assert message.code == Code.CONTENT
    assert message.opt.content_format == MediaType.TLV.value
    assert len(message.payload) > 0


def test_payload_encoder_single_resource(payload_encoder, model):
    message = payload_encoder.encode((3, 0, 1))
    assert message.code == Code.CONTENT
    assert message.opt.content_format == MediaType.TEXT.value
    assert message.payload.decode() == str(model.resource(3, 0, 1))


def test_payload_encoder_multiple_resource(payload_encoder, model):
    message = payload_encoder.encode((3, 0, 6))
    assert message.code == Code.CONTENT
    assert message.opt.content_format == MediaType.TLV.value
    assert len(message.payload) > 0


def test_payload_encode_decode_different_types(special_definition, special_data):
    model = ClientModel(definition_loader=special_definition, data_loader=special_data)
    encoder = PayloadEncoder(model)
    decoder = PayloadDecoder(model)
    payload = encoder.encode((1337,)).payload
    message, apply = decoder.decode((1337,), payload, MediaType.TLV.value)
    assert message.code == Code.CHANGED
    assert apply == special_data.load()
