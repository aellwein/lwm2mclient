#!/usr/bin/env python3
from setuptools import setup

setup(
    name='lwm2mclient',
    version='0.1.0+git',
    description='Lightweight M2M Client written in Python',
    author='Alexander Ellwein',
    author_email='alex.ellwein@gmail.com',
    license='MIT License',
    install_requires=[
        'aiocoap==0.4a1',
        'hexdump==3.3'
    ]
)
