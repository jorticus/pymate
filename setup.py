#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info[0] != 2:
    sys.stderr.write("Only Python 2 is supported! Please use Python 2!\n")
    sys.exit(1)


setup(
    name='pymate',
    version='v2.1',
    description='Outback MATE python interface',
    author='Jared',
    author_email='jared@jared.geek.nz',
    url='https://jared.geek.nz/pymate',
    keywords=['outback', 'mate', 'pymate'],
    classifiers=[],
    packages=['pymate']
)
