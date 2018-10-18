#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import codecs
import os

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.build_py import build_py


def _pre_install(dir):
    from subprocess import check_call
    check_call(['./setup.sh'], shell=True, cwd=os.getcwd())


class CustomInstall(install):
    def run(self):
        self.execute(_pre_install, (self.install_lib,),
                     msg='Running post install task')
        install.run(self)


class CustomDevelop(develop):
    def run(self):
        self.execute(_pre_install, (self.install_lib,),
                     msg='Running post install task')
        develop.run(self)


class CustomBuildPy(build_py):
    def run(self):
        _pre_install(None)
        build_py.run(self)


# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
try:
    with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except:
    # This happens when running tests
    long_description = None


setup(
    name='textworld',
    version='0.0.3',
    author='',
    cmdclass={
        'build_py': CustomBuildPy,
        'install': CustomInstall,
        'develop': CustomDevelop
    },
    packages=find_packages(),
    include_package_data=True,
    scripts=[
        'scripts/tw-data',
        'scripts/tw-play',
        'scripts/tw-make',
        'scripts/tw-stats',
    ],
    license='',
    zip_safe=False,
    description='Microsoft Textworld - A Text-based Learning Environment.',
    long_description=long_description,
    cffi_modules=['glk_build.py:ffibuilder'],
    setup_requires=['cffi>=1.0.0'],
    install_requires=codecs.open('requirements.txt', encoding='utf-8').readlines(),
    test_suite='nose.collector',
    tests_require=[
        'nose==1.3.7',
    ],
)
