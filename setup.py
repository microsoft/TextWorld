#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


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
    author='Microsoft Textworld',
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
    license='',
    zip_safe=False,
    url="https://github.com/microsoft/TextWorld",
    description="Microsoft Textworld - A Text-based Learning Environment.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    cffi_modules=["glk_build.py:ffibuilder"],
    setup_requires=['cffi>=1.0.0'],
    install_requires=open('requirements.txt').readlines(),
    test_suite='pytest',
    tests_require=[
        'pytest',
    ],
    extras_require={
        'vis': open('requirements-vis.txt').readlines(),
        'pddl': open('requirements-pddl.txt').readlines(),
        'full': open('requirements-full.txt').readlines(),
    },
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Life",
    ]
)
