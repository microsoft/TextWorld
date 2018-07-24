#!/usr/bin/env bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

set -ex
echo "Running setup.sh...";

# Generate parsers
tatsu textworld/logic/logic.ebnf -o textworld/logic/parser.py -G textworld/logic/model.py

cd textworld/thirdparty/

# Install command line Inform 7
if [ ! -e I7_6M62_Linux_all.tar.gz ]; then
    echo "Downloading Inform7 CLI"
    curl -LO http://inform7.com/download/content/6M62/I7_6M62_Linux_all.tar.gz
    if [ "${machine}" == 'Mac' ] && [ ! -e I7-6M62-OSX.dmg ]; then
        echo "Downloading Inform7 for Mac"
        curl -LO http://inform7.com/download/content/6M62/I7-6M62-OSX.dmg
    fi
fi
if [ ! -d inform7-6M62 ]; then
    tar xf I7_6M62_Linux_all.tar.gz
fi
(
    echo "Installing Inform7 CLI"
    cd inform7-6M62/
    ./install-inform7.sh --prefix $PWD
)

# Mount DMG if we're using a Mac
if [ "${machine}" == 'Mac' ]; then
    echo "Mounting Inform for Mac"
    hdiutil attach ./I7-6M62-OSX.dmg

    echo "Copying Mac compiled inform files"
    current_dir="`pwd`"
    cd /Volumes/Inform/Inform.app/Contents/MacOS
    /bin/cp -t "$current_dir/share/inform7/Compilers/" cBlorb inform6 Inform intest ni
    /bin/cp ./git "$current_dir/share/inform7/Interpreters/dumb-git"
    /bin/cp ./glulxe "$current_dir/share/inform7/Interpreters/dumb-glulxe"

    cd "$current_dir"

    echo "Unmounting Inform for Mac"
    hdiutil detach /Volumes/Inform/
fi

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
