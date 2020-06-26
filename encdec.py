#!/usr/bin/env python3

import logging
from enum import Enum
from math import log
from struct import pack, unpack

from aiocoap.message import Message
from aiocoap.numbers.codes import Code

import hexdump
from hexdump import hexdump
from model import ClientModel

logger = logging.getLogger('encoder')


class TlvType(Enum):
    OBJECT_INSTANCE = 0b00000000
    RESOURCE_INSTANCE = 0b01000000
    MULTIPLE_RESOURCE = 0b10000000
    RESOURCE_VALUE = 0b11000000


class MediaType(Enum):
    TEXT = 0
    LINK = 40
    OPAQUE = 42
    TLV = 11542
    JSON = 11543


# useful lambda to calculate the needed bytes from an integer
def needs_bytes(n): return 1 if n == 0 else int(log(abs(n), 256)) + 1


class TlvEncoder(object):
    def __init__(self):
        pass

    @staticmethod
    def encode_object(model, obj):
        if model.is_object_multi_instance(obj):
            _buf = bytearray()
            for inst in model.instances(obj):
                _buf.extend(TlvEncoder._instance_to_tlv(model, obj, inst))
            logging.debug(f'encode_object(): {hexdump(_buf, result="return")}')
            msg = Message(code=Code.CONTENT, payload=_buf,
                          content_format=MediaType.TLV.value)
            return msg
        else:
            # directly encode resources
            _inst = model.instances(obj)[0]
            _buf = bytearray()
            for res in model.resources(obj, _inst):
                if model.is_resource_readable(obj, _inst, res):
                    _buf.extend(TlvEncoder._resource_to_tlv(
                        model, obj, _inst, res))
            logging.debug(f'encode_object(): {hexdump(_buf, result="return")}')
            msg = Message(code=Code.CONTENT, payload=_buf,
                          content_format=MediaType.TLV.value)
            return msg

    @staticmethod
    def encode_instance(model, obj, inst):
        _buf = bytearray()
        for res in model.resources(obj, inst):
            if model.is_resource_readable(obj, inst, res):
                _buf.extend(TlvEncoder._resource_to_tlv(model, obj, inst, res))
        logging.debug(f'encode_instance(): {hexdump(_buf, result="return")}')
        msg = Message(code=Code.CONTENT, payload=_buf,
                      content_format=MediaType.TLV.value)
        return msg

    @staticmethod
    def encode_resource(model, obj, inst, res):
        if not model.is_resource_multi_instance(obj, inst, res):
            if model.is_resource_readable(obj, inst, res):
                # single resource queries are returned as TEXT (plain)
                _r = model.resource(obj, inst, res)
                _payload = str(_r).encode()
                logging.debug(
                    f'encode_resource(): {hexdump(_payload, result="return")}')
                return Message(code=Code.CONTENT, payload=_payload, content_format=MediaType.TEXT.value)
            else:
                return Message(code=Code.METHOD_NOT_ALLOWED)
        else:
            # multi-resource
            if not model.is_resource_readable(obj, inst, res):
                return Message(code=Code.METHOD_NOT_ALLOWED)
            _payload = TlvEncoder._resource_to_tlv(model, obj, inst, res)
            logging.debug(
                f'encode_resource(): {hexdump(_payload, result="return")}')
            msg = Message(code=Code.CONTENT, payload=_payload,
                          content_format=MediaType.TLV.value)
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
                raise TypeError(
                    f'multiple resource {obj}/{inst}/{res} must be of "dict" type')
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
        result.extend(_id.to_bytes(1, byteorder='big') if _id <
                      256 else _id.to_bytes(2, byteorder='big'))
        if _len >= 8:
            if _len < 256:
                result.extend(_len.to_bytes(1, byteorder='big'))
            elif _len < 65536:
                result.extend(_len.to_bytes(2, byteorder='big'))
            else:
                msb = _len & 0xFF0000 >> 16
                result.extend(msb.to_bytes(1, byteorder='big'))
                result.extend((_len & 0xFFFF).to_bytes(2, byteorder='big'))
        result.extend(payload)
        return result

    @staticmethod
    def _get_resource_payload(model, obj, inst, res, res_idx=None):
        _type = model.definition[obj]['resourcedefs'][str(res)]['type']
        if res_idx is not None:
            _content = model.resource(obj, inst, res)[res_idx]
            logger.debug(
                f'_resource_to_tlv(): {obj}/{inst}/{res}, idx={res_idx}, type={_type}, content="{_content}"')
        else:
            _content = model.resource(obj, inst, res)
            logger.debug(
                f'_resource_to_tlv(): {obj}/{inst}/{res}, type={_type}, content="{_content}"')
        if _type == 'integer':
            i = int(_content)
            _payload = i.to_bytes(
                int(i.bit_length() / 8) + 1, byteorder='big', signed=True)
        elif _type == 'string':
            _payload = _content.encode()
        elif _type == 'float':
            f = float(_content)
            if float.fromhex('0x0.000002P-126') <= f <= float.fromhex('0x1.fffffeP+127'):
                # fits in a float
                _payload = pack('>f', f)
            else:
                # use double
                _payload = pack('>d', f)
        elif _type == 'boolean':
            _payload = b'\x01' if _content else b'\x00'
        elif _type == 'time':
            _payload = pack('>q', int(_content))
        elif _type == 'opaque':
            _payload = bytearray.fromhex(_content)
        else:
            raise TypeError(
                f'unknown resource type: {_type}. Must be one of (integer,string,float,boolean,time,opaque)')
        logger.debug(f'payload: {hexdump(_payload, result="return")}')
        return _payload


class DecoderException(BaseException):
    def __init__(self, message):
        super(DecoderException, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class TextDecoder(object):
    def __init__(self):
        pass

    @staticmethod
    def decode(_model, path, payload):
        _obj = path[0]
        _inst = path[1]
        _res = path[2]
        result = dict()
        result[_obj] = dict()
        result[_obj][_inst] = dict()
        _payload = payload.decode()
        _type = _model.definition[_obj]['resourcedefs'][str(_res)]['type']
        if _type == 'integer':
            result[_obj][_inst][_res] = int(_payload)
        elif _type == 'string':
            result[_obj][_inst][_res] = _payload
        elif _type == 'float':
            result[_obj][_inst][_res] = float(_payload)
        elif _type == 'boolean':
            result[_obj][_inst][_res] = True if _payload == '1' else False
        elif _type == 'time':
            result[_obj][_inst][_res] = int(_payload)
        elif _type == 'opaque':
            result[_obj][_inst][_res] = payload.hex()
        else:
            raise TypeError(f'unknown type: {_type}')
        logging.debug(f'result of TEXT decoding: {result}')
        return result


class TlvDecoder(object):
    def __init__(self):
        pass

    @staticmethod
    def decode(_model, path, payload):
        logger.debug(
            f'decode(path={path}, payload={hexdump(payload, result="return")})')
        _payload = payload
        result = dict()
        while len(_payload) != 0:
            _id, _value, _type, _payload = TlvDecoder._decode(path, _payload)
            _value = TlvDecoder.value_from_bytes(
                _model, (path[0], path[1], str(_id),), _value)
            result = dict(TlvDecoder.mergedicts(result, _value))
        logger.info(f'decode result: {result}')
        return result

    @staticmethod
    def value_from_bytes(_model, path, payload):
        _obj = path[0]
        _inst = path[1]
        _res = path[2]
        result = dict()
        result[_obj] = dict()
        result[_obj][_inst] = dict()
        _type = _model.definition[_obj]['resourcedefs'][str(_res)]['type']
        if _type == 'integer':
            result[_obj][_inst][_res] = int.from_bytes(
                payload, byteorder='big')
        elif _type == 'string':
            result[_obj][_inst][_res] = payload.decode()
        elif _type == 'float':
            result[_obj][_inst][_res] = unpack('f', payload)
        elif _type == 'boolean':
            result[_obj][_inst][_res] = True if payload[0] == 1 else False
        elif _type == 'time':
            result[_obj][_inst][_res] = int.from_bytes(
                payload, byteorder='big')
        elif _type == 'opaque':
            result[_obj][_inst][_res] = payload.hex()
        else:
            raise TypeError(f'unknown type: {_type}')
        logging.debug(f'decoding result: {result}')
        return result

    @staticmethod
    def mergedicts(dict1, dict2):
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

    @staticmethod
    def _decode(path, payload):
        try:
            _type = payload[0]
        except IndexError:
            raise DecoderException('invalid TLV length')
        _len_type = _type >> 3 & 0b11
        _len = None
        if _len_type == 0:
            _len = _type & 0b111
            logger.debug(f'Value length: {_len} bytes')
        elif _len_type == 1:
            logger.debug(f'length\'s length: 8 bits')
        elif _len_type == 2:
            logger.debug(f'length\'s length: 16 bits')
        elif _len_type == 3:
            logger.debug(f'length\'s length: 24 bits')
        id_len = _type >> 5 & 1
        try:
            _payload = payload[1:]
        except IndexError:
            raise DecoderException(
                'unable to determine ID from invalid payload')

        _id = None
        if id_len == 1:
            logger.debug('ID: 16 bits')
            try:
                _id = int.from_bytes(_payload[0:2], byteorder='big')
                logger.debug(f'ID: {_id}')
                _payload = _payload[2:]
            except IndexError:
                raise DecoderException('missing ID bytes in TLV')
        elif id_len == 0:
            logger.debug('ID length: 8 bits')
            try:
                _id = int.from_bytes(_payload[0:1], byteorder='big')
                logger.debug(f'ID: {_id}')
                _payload = _payload[1:]
            except IndexError:
                raise DecoderException('missing ID bytes in TLV')
        else:
            raise DecoderException('invalid ID length')
        try:
            if _len is None:
                _len = int.from_bytes(_payload[0:_len_type], byteorder='big')
                logger.info(f'value length: {_len}')
                _payload = _payload[_len_type:]
            _value = _payload[0:_len]
            logger.debug(f'value: {hexdump(_value, result="return")}')
        except IndexError:
            raise DecoderException('not enough bytes for TLV value in payload')

        if _type >> 6 == 0b00:
            # OBJECT_INSTANCE
            logger.debug('type = OBJECT_INSTANCE')
            pass
        elif _type >> 6 == 0b01:
            # RESOURCE_INSTANCE
            logger.debug('type = RESOURCE_INSTANCE')
            pass
        elif _type >> 6 == 0b10:
            # MULTIPLE_RESOURCE
            logger.debug('type = MULTIPLE_RESOURCE')
            pass
        elif _type >> 6 == 0b11:
            # RESOURCE_VALUE
            logger.debug('type = RESOURCE_VALUE')
            pass
        else:
            raise DecoderException(f'invalid TLV type: {_type >> 6}')
        return _id, _value, _type, _payload[_len:]


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
        if not self.model.is_path_valid(path):
            return Message(code=Code.NOT_FOUND), None
        try:
            if content_format == MediaType.TLV.value:
                return Message(code=Code.CHANGED), TlvDecoder.decode(self.model, path, payload)
            elif content_format == MediaType.TEXT.value:
                if len(path) != 3 or self.model.is_resource_multi_instance(path[0], path[1], path[2]):
                    raise Exception(
                        'TEXT format should only be used for single non-multiple resource')
                return Message(code=Code.CHANGED), TextDecoder.decode(self.model, path, payload)
            else:
                raise Exception(
                    f'unsupported content format: {content_format}')
        except DecoderException as e:
            return Message(code=Code.BAD_REQUEST, payload=e.message.encode()), None


if __name__ == '__main__':
    model = ClientModel()
    encoder = PayloadEncoder(model)
    logger.debug(f'encode: {encoder.encode(("3",))}')
