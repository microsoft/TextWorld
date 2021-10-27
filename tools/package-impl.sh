#!/bin/bash

# Based on https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh

set -e

cd /usr/src/TextWorld

for PYTHON in /opt/python/cp3{6,7,8,9}*/bin/python; do
    $PYTHON setup.py bdist_wheel -d wheelhouse
done

for WHEEL in wheelhouse/textworld-*.whl; do
    auditwheel repair $WHEEL -w dist
done
