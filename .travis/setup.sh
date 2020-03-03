#!/bin/bash

set -e

if [[ $TRAVIS_OS_NAME == "osx" ]]; then
    # Disable Homebrew's auto-update
    # See https://discuss.circleci.com/t/brew-link-step-failing-on-python-dependency/33925/8
    brew unlink python@2
    brew update
    brew tap homebrew/cask
    brew cask install google-chrome chromedriver
    brew install graphviz

    pip3 install virtualenv
    virtualenv -p python3 venv
    . ./venv/bin/activate
fi

pip install -r requirements-full.txt
pip install .
pip install nose coverage codecov
