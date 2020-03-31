#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info[0] != 2:
    sys.stderr.write("Only Python 2 is supported! Please use Python 2!\n")
    sys.exit(1)


setup(
    name='pymate',
    version='v2.2',
    description='Outback MATE python interface',
    author='Jared',
    author_email='jared@jared.geek.nz',
    url='https://github.com/jorticus/pymate',
    keywords=['outback', 'mate', 'pymate'],
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
    packages=['pymate', 'pymate.matenet'],
    install_requires=['pyserial'],
    python_requires='>=2.7,!=3.*',
)
