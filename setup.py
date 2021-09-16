#!/usr/bin/env python

import sys
from setuptools import setup

setup(
    name='pymate',
    version='v3.0',
    description='Outback MATE python interface',
    author='Jared',
    author_email='jared@jared.geek.nz',
    url='https://github.com/jorticus/pymate',
    keywords=['outback', 'mate', 'pymate'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
    packages=['pymate', 'pymate.matenet'],
    install_requires=['pyserial'],
    python_requires='>=3.0,!=2.*',
)
