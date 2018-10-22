#!/bin/bash

set -ex

export PATH=$PWD/glulx/Git-Glulx:$PATH

pip3 install -v .
pip3 install nose coverage
nosetests -sv --with-xunit --with-coverage --cover-xml --cover-html --cover-package textworld