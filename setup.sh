#!/usr/bin/env bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


set -ex
echo "Running setup.sh...";

# Generate parsers
tatsu textworld/logic/logic.ebnf -o textworld/logic/parser.py -G textworld/logic/model.py

cd textworld/thirdparty/

# Install command line Inform 7
if [ ! -e I7_6M62_Linux_all.tar.gz ]; then
    echo "Downloading Inform7 CLI"
    curl -LO http://inform7.com/download/content/6M62/I7_6M62_Linux_all.tar.gz
fi
if [ ! -d inform7-6M62 ]; then
    tar xf I7_6M62_Linux_all.tar.gz
fi
(
    echo "Installing Inform7 CLI"
    cd inform7-6M62/
    ./install-inform7.sh --prefix $PWD
)

# Install a modified fork of Frotz and build it specifically for interaction with the command line
if [ ! -d frotz ]; then
    echo "Installing frotz"
    git clone https://github.com/danielricks/frotz.git
fi
(
    cd frotz/
    make -B dumb
)

# Install modified fork of Glulx and build it - we have this one locally
(
    echo "Installing cheapglk"
    cd glulx/cheapglk
    make -B
)
(
    echo "Installing git-glulx-ml"
    cd glulx/Git-Glulx
    make -B
)
