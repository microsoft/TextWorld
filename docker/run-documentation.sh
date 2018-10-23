#!/bin/bash

set -ex

pip3 install -e .

pushd docs
pip3 install -r requirements.txt || true
make html
popd
