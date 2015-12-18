#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015 Alexander Ellwein
#
# lwm2mclient is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import sys
from setuptools import setup

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

setup(
        name="lwm2mclient",
        version="0.1.0+git",
        description="Lightweight M2M Client written in Python",
        author="Alexander Ellwein",
        author_email="alex.ellwein@gmail.com",
        license="MIT License",
        install_requires=["aiocoap>=0.2", "hexdump"],
        setup_requires=["pytest-runner"],
        tests_require=["pytest"]
)
