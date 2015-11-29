#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from enum import Enum
from math import log
from struct import pack
from aiocoap.message import Message
from aiocoap.numbers.codes import Code
from hexdump import hexdump
from model import ClientModel

logger = logging.getLogger("encoder")


class TlvType(Enum):
    OBJECT_INSTANCE = 0b00000000
    RESOURCE_INSTANCE = 0b01000000
    MULTIPLE_RESOURCE = 0b10000000
    RESOURCE_VALUE = 0b11000000


class MediaType(Enum):
    LINK = 40
    TEXT = 1541
    TLV = 1542
    JSON = 1543
    OPAQUE = 1544


# useful lambda to calculate the needed bytes from an integer
needs_bytes = lambda n: 1 if n == 0 else int(log(abs(n), 256)) + 1


class TlvEncoder(object):
    def __init__(self):
        pass

    @staticmethod
    def encode_object(model, obj):
        if model.is_object_multi_instance(obj):
            _buf = bytearray()
            for inst in model.instances(obj):
                _buf.extend(TlvEncoder._instance_to_tlv(model, obj, inst))
            logging.debug("encode_object(): %s" % hexdump(_buf, result="return"))
            msg = Message(code=Code.CONTENT, payload=_buf)
            msg.opt.content_format = MediaType.TLV.value
            return msg
        else:
            # directly encode resources
            _inst = model.instances(obj)[0]
            _buf = bytearray()
            for res in model.resources(obj, _inst):
                if model.is_resource_readable(obj, _inst, res):
                    _buf.extend(TlvEncoder._resource_to_tlv(model, obj, _inst, res))
            logging.debug("encode_object(): %s" % hexdump(_buf, result="return"))
            msg = Message(code=Code.CONTENT, payload=_buf)
            msg.opt.content_format = MediaType.TLV.value
            return msg

    @staticmethod
    def encode_instance(model, obj, inst):
        _buf = bytearray()
        for res in model.resources(obj, inst):
            if model.is_resource_readable(obj, inst, res):
                _buf.extend(TlvEncoder._resource_to_tlv(model, obj, inst, res))
        logging.debug("encode_instance(): %s" % hexdump(_buf, result="return"))
        msg = Message(code=Code.CONTENT, payload=_buf)
        msg.opt.content_format = MediaType.TLV.value
        return msg

    @staticmethod
    def encode_resource(model, obj, inst, res):
        if not model.is_resource_multi_instance(obj, inst, res):
            if model.is_resource_readable(obj, inst, res):
                # single resource queries are returned as TEXT (plain)
                _r = model.resource(obj, inst, res)
                _payload = str(_r).encode()
                logging.debug("encode_resource(): %s" % hexdump(_payload, result="return"))
                return Message(code=Code.CONTENT, payload=_payload)
            else:
                return Message(code=Code.METHOD_NOT_ALLOWED)
        else:
            # multi-resource
            if not model.is_resource_readable(obj, inst, res):
                return Message(code=Code.METHOD_NOT_ALLOWED)
            _payload = TlvEncoder._resource_to_tlv(model, obj, inst, res)
            logging.debug("encode_resource(): %s" % hexdump(_payload, result="return"))
            msg = Message(code=Code.CONTENT, payload=_payload)
            msg.opt.content_format = MediaType.TLV.value
            return msg

    @staticmethod
    def _instance_to_tlv(model, obj, inst):
        _buf = bytearray()
        for res in model.resources(obj, inst):
            if model.is_resource_readable(obj, inst, res):
                _buf.extend(TlvEncoder._resource_to_tlv(model, obj, inst, res))
        return TlvEncoder._pack(TlvType.OBJECT_INSTANCE, int(inst), payload=_buf)

    @staticmethod
    def _resource_to_tlv(model, obj, inst, res):
        _r = model.resource(obj, inst, res)
        if model.is_resource_multi_instance(obj, inst, res):
            if type(_r) != dict:
                raise TypeError("multiple resource %s/%s/%s must be of 'dict' type" % (obj, inst, res))
            # MULTIPLE_RESOURCE ( RESOURCE_INSTANCE, RESOURCE_INSTANCE... )
            _buf = bytearray()
            for _res_inst in _r.keys():
                _buf.extend(TlvEncoder._pack(TlvType.RESOURCE_INSTANCE, int(_res_inst),
                                             TlvEncoder._get_resource_payload(model, obj, inst, res, _res_inst)))
            return TlvEncoder._pack(TlvType.MULTIPLE_RESOURCE, int(res), _buf)
        else:
            # RESOURCE_VALUE (single)
            return TlvEncoder._pack(TlvType.RESOURCE_VALUE, int(res),
                                    TlvEncoder._get_resource_payload(model, obj, inst, res))

    @staticmethod
    def _pack(tlv_type, _id, payload):
        result = bytearray()
        _type = int(tlv_type.value)
        _len = len(payload)
        _type |= 0b000000 if 1 == needs_bytes(_id) else 0b100000
        if _len < 8:
            _type |= _len
        elif needs_bytes(_len) == 1:
            _type |= 0b00001000
        elif needs_bytes(_len) == 2:
            _type |= 0b00010000
        else:
            _type |= 0b00011000
        result.append(_type)
        result.extend(_id.to_bytes(1, byteorder="big") if _id < 256 else _id.to_bytes(2, byteorder="big"))
        if _len >= 8:
            if _len < 256:
                result.extend(_len.to_bytes(1, byteorder="big"))
            elif _len < 65536:
                result.extend(_len.to_bytes(2, byteorder="big"))
            else:
                msb = _len & 0xFF0000 >> 16
                result.extend(msb.to_bytes(1, byteorder="big"))
                result.extend((_len & 0xFFFF).to_bytes(2, byteorder="big"))
        result.extend(payload)
        return result

    @staticmethod
    def _get_resource_payload(model, obj, inst, res, res_idx=None):
        _type = model.definition[obj]["resourcedefs"][str(res)]["type"]
        if res_idx is not None:
            _content = model.resource(obj, inst, res)[res_idx]
            logger.debug("_resource_to_tlv(): %s/%s/%s, idx=%s, type=%s, content=\"%s\"" % (
                obj, inst, res, res_idx, _type, _content))
        else:
            _content = model.resource(obj, inst, res)
            logger.debug("_resource_to_tlv(): %s/%s/%s, type=%s, content=\"%s\"" % (obj, inst, res, _type, _content))
        if _type == "integer":
            i = int(_content)
            _payload = i.to_bytes(int(i.bit_length() / 8) + 1, byteorder="big", signed=True)
        elif _type == "string":
            _payload = _content.encode()
        elif _type == "float":
            f = float(_content)
            if float.fromhex("0x0.000002P-126") <= f <= float.fromhex("0x1.fffffeP+127"):
                # fits in a float
                _payload = pack(">f", f)
            else:
                # use double
                _payload = pack(">d", f)
        elif _type == "boolean":
            _payload = b'\x01' if _content.upper() == "TRUE" else b'\x00'
        elif _type == "time":
            _payload = pack(">q", int(_content))
        elif _type == "opaque":
            _payload = bytearray.fromhex(_content)
        else:
            raise TypeError(
                "unknown resource type: %s. Must be one of (integer,string,float,boolean,time,opaque)" % _type)
        logger.debug("payload: %s" % hexdump(_payload, result="return"))
        return _payload


class TextDecoder(object):
    def __init__(self):
        pass

    @staticmethod
    def decode(_model, path, payload):
        if len(path) != 3 or _model.is_resource_multi_instance(path[0], path[1], path[2]):
            raise Exception("TEXT format should only be used for single non-multiple resource")
        _obj = path[0]
        _inst = path[1]
        _res = path[2]
        result = dict()
        result[_obj] = dict()
        result[_obj][_inst] = dict()
        _payload = payload.decode()
        _type = _model.definition[_obj]["resourcedefs"][str(_res)]["type"]
        if _type == "integer":
            result[_obj][_inst][_res] = int(_payload)
        elif _type == "string":
            result[_obj][_inst][_res] = _payload
        elif _type == "float":
            result[_obj][_inst][_res] = float(_payload)
        elif _type == "boolean":
            result[_obj][_inst][_res] = True if _payload == "1" else False
        elif _type == "time":
            result[_obj][_inst][_res] = int(_payload)
        elif _type == "opaque":
            result[_obj][_inst][_res] = payload.hex()
        else:
            raise TypeError("unknown type: %s" % _type)
        logging.debug("result of TEXT decoding: {}".format(result))
        return result


class TlvDecoder(object):
    def __init__(self):
        pass

    @staticmethod
    def decode(_model, path, payload):
        logger.debug("decode(path=%s, payload=%s)" % (path, payload))


class PayloadEncoder(object):
    def __init__(self, _model):
        self.model = _model

    def encode(self, path):
        if not self.model.is_path_valid(path):
            return Message(code=Code.NOT_FOUND)
        path_len = len(path)
        if path_len == 1:
            # read on whole object (TLV)
            return TlvEncoder.encode_object(self.model, path[0])
        elif path_len == 2:
            # read on instance (TLV)
            return TlvEncoder.encode_instance(self.model, path[0], path[1])
        elif path_len == 3:
            return TlvEncoder.encode_resource(self.model, path[0], path[1], path[2])
        else:
            return Message(code=Code.BAD_REQUEST)


class PayloadDecoder(object):
    def __init__(self, _model):
        self.model = _model

    def decode(self, path, payload, content_format):
        if content_format == MediaType.TLV.value:
            return TlvDecoder.decode(self.model, path, payload)
        elif content_format == MediaType.TEXT.value:
            return TextDecoder.decode(self.model, path, payload)
        else:
            raise Exception("unsupported content format: %s" % content_format)


if __name__ == '__main__':
    model = ClientModel()
    pe = PayloadEncoder(model)
    logger.debug("encode: {}".format(pe.encode(("3",))))
