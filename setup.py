#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.build_py import build_py
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    """
    Force wheel to be marked as non-pure (platform-specific) even though we
    don't compile extension modules, because we bundle OS-specific binaries.
    """
    def has_ext_modules(self):
        return True


def _pre_install(dir):
    from subprocess import check_call
    check_call(['./setup.sh'], shell=True, cwd=os.getcwd())


class CustomInstall(install):
    def run(self):
        self.execute(_pre_install, (self.install_lib,),
                     msg="Running post install task")
        install.run(self)


class CustomDevelop(develop):
    def run(self):
        self.execute(_pre_install, (self.install_lib,),
                     msg="Running post install task")
        develop.run(self)


class CustomBuildPy(build_py):
    def run(self):
        _pre_install(None)
        build_py.run(self)


setup(
    name='textworld',
    version=open(os.path.join("textworld", "version.py")).readlines()[0].split("=")[-1].strip("' \n"),
    distclass=BinaryDistribution,
    cmdclass={
        'build_py': CustomBuildPy,
        'install': CustomInstall,
        'develop': CustomDevelop
    },
    packages=find_packages(),
    include_package_data=True,
    scripts=[
        "scripts/tw-data",
        "scripts/tw-play",
        "scripts/tw-make",
        "scripts/tw-stats",
        "scripts/tw-extract",
        "scripts/tw-view",
    ],
    zip_safe=False,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=open('requirements.txt').readlines(),
    test_suite='pytest',
    tests_require=[
        'pytest',
    ],
    extras_require={
        'vis': open('requirements-vis.txt').readlines(),
        'pddl': open('requirements-pddl.txt').readlines(),
        'full': open('requirements-full.txt').readlines(),
        'dev': open('requirements-dev.txt').readlines(),
    }
)
