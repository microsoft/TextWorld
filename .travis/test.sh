#!/bin/bash

set -e

if [[ $TRAVIS_OS_NAME == "osx" ]]; then
    . ./venv/bin/activate
fi

nosetests -sv --with-xunit --with-coverage --cover-xml --cover-html --cover-package textworld
