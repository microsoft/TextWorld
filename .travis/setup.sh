#!/bin/bash

set -e

if [[ $TRAVIS_OS_NAME == "osx" ]]; then
    brew update
    brew tap homebrew/cask
    brew cask install google-chrome chromedriver
    brew install graphviz

    pip3 install virtualenv
    virtualenv -p python3 venv
    . ./venv/bin/activate
fi

pip install .
pip install nose coverage codecov
