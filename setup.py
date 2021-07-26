#!/usr/bin/env python

import sys
from setuptools import setup

setup(
    name='pymate',
    version='v2.1',
    description='Outback MATE python interface',
    author='Jared',
    author_email='jared@jared.geek.nz',
    url='https://jared.geek.nz/pymate',
    keywords=['outback', 'mate', 'pymate'],
    classifiers=[],
    packages=['pymate', 'pymate.matenet'],
    install_requires=['pyserial']
)
