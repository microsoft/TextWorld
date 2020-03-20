#!/bin/bash

# Based on https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh

set -e

cd /usr/src/TextWorld

for PYTHON in /opt/python/cp3[5-8]*/bin/python; do
    $PYTHON setup.py bdist_wheel -d wheelhouse
done

for WHEEL in wheelhouse/textworld-*.whl; do
    auditwheel repair $WHEEL -w dist
done
