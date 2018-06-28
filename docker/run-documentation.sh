#!/bin/bash

set -ex

pip3 install -e .[prompt,vis]

pushd docs
pip3 install -r requirements.txt || true
make html
popd
