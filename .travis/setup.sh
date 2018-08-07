#!/bin/bash

set -e

if [[ $TRAVIS_OS_NAME == "osx" ]]; then
    brew tap homebrew/cask
    brew cask install google-chrome chromedriver

    pip3 install virtualenv
    virtualenv -p python3 venv
    . ./venv/bin/activate
fi

pip install .[prompt,vis]
pip install nose coverage
