#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

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


def test_payload_decoder_content_type_tlv(payload_decoder):
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
