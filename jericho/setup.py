# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from setuptools import setup
from setuptools.command.install import install
from distutils.command.build import build
from distutils.core import setup, Extension
import os.path, sys
import subprocess

BASEPATH = os.path.dirname(os.path.abspath(__file__))
FROTZPATH = os.path.join(BASEPATH, 'frotz')
subprocess.check_call(['make', 'clean'], cwd=FROTZPATH)
subprocess.check_call(['make', 'library', '-j', '4'], cwd=FROTZPATH)

frotz_c_lib = 'jericho/libfrotz.so'
if not os.path.isfile(frotz_c_lib):
    print('ERROR: Unable to find required library %s.'%(frotz_c_lib))
    sys.exit(1)

setup(name='jericho',
      version='1.0',
      install_requires=[],
      description='A python interface to text-based adventure games.',
      author='Matthew Hausknecht',
      packages=['jericho'],
      include_package_data=True,
      package_dir={'jericho': 'jericho'},
      package_data={'jericho': ['libfrotz.so']})
