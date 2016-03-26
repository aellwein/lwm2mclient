#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2016 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

from enum import Enum


class TlvType(Enum):
    """
    TLV types, used in TLV format as described in LWM2M Technical Specification.
    """
    OBJECT_INSTANCE = 0b00000000
    RESOURCE_INSTANCE = 0b01000000
    MULTIPLE_RESOURCE = 0b10000000
    RESOURCE_VALUE = 0b11000000


class MediaType(Enum):
    """
    Acknowledged media types (from content format CoAP option).
    """
    LINK = 40
    TEXT = 1541
    TLV = 1542
    JSON = 1543
    OPAQUE = 1544
