#!/usr/bin/env python3
from importlib.metadata import entry_points

from setuptools import find_packages, setup

setup(
    name='lwm2mclient',
    version='0.1.0+git',
    description='Lightweight M2M Client written in Python',
    url='https://github.com/aellwein/lwm2mclient',
    author='Alexander Ellwein',
    author_email='alex.ellwein@gmail.com',
    license='MIT License',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'lwm2m': [
            'client/data/model.yml'
        ]
    },
    entry_points={
        'console_scripts': [
            'lwm2mclient=lwm2m.client.client:main',
        ]
    },
)
