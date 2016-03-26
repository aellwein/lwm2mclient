#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import logging
from aiocoap.message import Message
from aiocoap.numbers.codes import Code
from hexdump import hexdump
from struct import unpack

from common import MediaType

logger = logging.getLogger("decoder")


class ContentFormatException(BaseException):
    """
    This exception is raised, if a given content format is either invalid or it cannot be applied
    for a specified path (for instance, a TEXT format cannot be applied for multi-instance resource).
    """

    def __init__(self, message):
        super(ContentFormatException, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class DecoderException(BaseException):
    """
    This exception can be raised by a decoder while decoding a malformed content.
    """

    def __init__(self, message):
        super(DecoderException, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class TextDecoder:
    """
    Decoder which is able to decode a payload in TEXT (UTF-8 coded text) format.
    """

    def __init__(self, model):
        """
        Creates a new decoder for TEXT format.
        :param model: client data model to use
        """
        self.model = model

    def decode(self, path, payload):
        """
        Decode a payload for the given path.
        :param path: path of the resource
        :param payload: payload to be decoded
        :return: dictionary containing decoded value, which can be directly applied to the model data.
        """
        _obj = str(path[0])
        _inst = str(path[1])
        _res = str(path[2])
        result = dict()
        result[_obj] = dict()
        result[_obj][_inst] = dict()
        try:
            _payload = payload.decode()
        except UnicodeDecodeError as e:
            raise DecoderException(e.reason)
        _type = self.model.definition[_obj]["resourcedefs"][_res]["type"]
        converter = dict(integer=lambda p: int(p),
                         string=lambda p: p,
                         float=lambda p: float(p),
                         boolean=lambda p: True if p == "1" else False,
                         time=lambda p: int(p),
                         opaque=lambda p: p.hex())
        try:
            result[_obj][_inst][_res] = converter[_type](_payload)
        except KeyError:
            raise TypeError("unknown type: %s" % _type)
        logging.debug("result of TEXT decoding: {}".format(result))
        return result


class TlvDecoder:
    """
    Decoder which is able to decode a Type-Length-Value (TLV) format.
    """

    def __init__(self, model):
        """
        Creates a new decoder for TLV format.
        :param model: client data model to use
        """
        self.model = model

    def decode(self, path, payload):
        """
        Decodes a given TLV payload.
        :param path: path of the resource to be decoded
        :param payload: TLV payload
        :return: a dictionary containing decoded object instances/resources.
        """
        logger.debug("decode(path=%s, payload=%s)" % (path, hexdump(payload, result="return")))
        _payload = payload
        result = dict()
        for _value in self._decode_gen(_payload):
            result = dict(TlvDecoder.mergedicts(result, _value))
        logger.debug("decode result: %s" % result)
        return result

    def _decode_gen(self, payload):
        """
        Recursive generator which decodes TLV-encoded values from payload.
        :param payload: payload to encode from
        :return: dictionary containing decoded values
        """
        if len(payload) == 0:
            return {}
        _payload = payload
        _type = _payload[0]
        if _type >> 6 == 0b00:
            # OBJECT_INSTANCE
            logger.debug("type = OBJECT_INSTANCE")
        elif _type >> 6 == 0b01:
            # RESOURCE_INSTANCE
            logger.debug("type = RESOURCE_INSTANCE")
        elif _type >> 6 == 0b10:
            # MULTIPLE_RESOURCE
            logger.debug("type = MULTIPLE_RESOURCE")
        elif _type >> 6 == 0b11:
            # RESOURCE_VALUE
            logger.debug("type = RESOURCE_VALUE")
        else:
            raise DecoderException("invalid TLV type: {}".format(_type >> 6))
        _len_type = _type >> 3 & 0b11
        _len = None
        if _len_type == 0:
            _len = _type & 0b111
            logger.debug("Value length: %d bytes" % _len)
        elif _len_type == 1:
            logger.debug("length's length: 8 bits")
        elif _len_type == 2:
            logger.debug("length's length: 16 bits")
        elif _len_type == 3:
            logger.debug("length's length: 24 bits")
        id_len = _type >> 5 & 1
        try:
            _payload = payload[1:]
        except IndexError:
            raise DecoderException("buffer is malformed: missing ID")

        _id = None
        if id_len == 1:
            logger.debug("ID: 16 bits")
            try:
                _id = int.from_bytes(_payload[0:2], byteorder="big")
                logger.debug("ID: %d" % _id)
                _payload = _payload[2:]
            except IndexError:
                raise DecoderException("missing ID bytes in TLV")
        elif id_len == 0:
            logger.debug("ID length: 8 bits")
            try:
                _id = int.from_bytes(_payload[0:1], byteorder="big")
                logger.debug("ID: %d" % _id)
                _payload = _payload[1:]
            except IndexError:
                raise DecoderException("missing ID bytes in TLV")
        else:
            raise DecoderException("invalid ID length")
        try:
            if _len is None:
                _len = int.from_bytes(_payload[0:_len_type], byteorder="big")
                logger.info("value length: %d" % _len)
                _payload = _payload[_len_type:]
            _value = _payload[0:_len]
            logger.debug("value: %s" % hexdump(_value, result="return"))
        except IndexError:
            raise DecoderException("not enough bytes for TLV value in payload")

    @staticmethod
    def _get_length(_type, payload):
        _len_type = _type >> 3 & 0b11
        _len = None
        if _len_type == 0:
            _len = _type & 0b111
            logger.debug("Value length: %d bytes" % _len)
        elif _len_type == 1:
            logger.debug("length's length: 8 bits")
        elif _len_type == 2:
            logger.debug("length's length: 16 bits")
        elif _len_type == 3:
            logger.debug("length's length: 24 bits")



    @staticmethod
    def _get_id(payload):
        pass

    @staticmethod
    def get_value(_model, path, payload):
        _obj = str(path[0])
        _inst = str(path[1])
        _res = str(path[2])
        try:
            _type = _model.definition[_obj]["resourcedefs"][_res]["type"]
        except KeyError:
            raise DecoderException("invalid resource path: /%s/%s/%s" % (_obj, _inst, _res))
        converter = dict(integer=lambda p: int.from_bytes(p, byteorder="big"),
                         string=lambda p: p.decode(),
                         float=lambda p: unpack("f", p),
                         boolean=lambda p: True if p[0] == 1 else False,
                         time=lambda p: int.from_bytes(p, byteorder="big"),
                         opaque=lambda p: p.hex())
        try:
            return converter[_type](payload)
        except KeyError:
            raise TypeError("unknown type: %s" % _type)

    @staticmethod
    def mergedicts(dict1, dict2):
        """
        Generator which performs a deep merge of given dictionaries.
        :param dict1: dict to merge
        :param dict2: dict to merge
        :return: merged dicts
        """
        for k in set(dict1.keys()).union(dict2.keys()):
            if k in dict1 and k in dict2:
                if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                    yield (k, dict(TlvDecoder.mergedicts(dict1[k], dict2[k])))
                else:
                    yield (k, dict2[k])
            elif k in dict1:
                yield (k, dict1[k])
            else:
                yield (k, dict2[k])


class PayloadDecoder:
    """
    Payload decoder takes a payload received from a server and decodes it into value, which is to be applied
    to client's data. For LWM2M payload, there are different formats, such as TEXT or TLV (Type-Length-Value coded).
    These formats are reflected in MediaType enumeration.
    """

    def __init__(self, model):
        """
        Creates a payload decoder with given client model.
        :param model: client model to use
        """
        self.model = model
        self.text_decoder = TextDecoder(model)
        self.tlv_decoder = TlvDecoder(model)

    def decode(self, path, payload, content_format):
        """
        Decodes the given payload, in given content format for given path.
        :param path: path of the object, instance or resource to decode payload for
        :param payload: byte payload to decode
        :param content_format: content format as reflected in MediaType enum.
        :return: Message with appropriate error code and data to apply to the model,
                 as accepted by ClientModel.apply() function. If error code is not CHANGED,
                 no data is returned.
        """
        if not self.model.is_path_valid(path):
            return Message(code=Code.NOT_FOUND), None
        try:
            if content_format == MediaType.TLV.value:
                return Message(code=Code.CHANGED), self.tlv_decoder.decode(path, payload)
            elif content_format == MediaType.TEXT.value:
                if len(path) != 3 or self.model.is_resource_multi_instance(path[0], path[1], path[2]):
                    raise ContentFormatException("TEXT format should only be used for single non-multiple resource")
                return Message(code=Code.CHANGED), self.text_decoder.decode(path, payload)
            else:
                raise ContentFormatException("unsupported content format: %s" % content_format)
        except DecoderException as e:
            return Message(code=Code.BAD_REQUEST, payload=e.message.encode()), None
