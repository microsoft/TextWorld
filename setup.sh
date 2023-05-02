#!/usr/bin/env bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

set -ex
echo "Running setup.sh...";

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGW;;
    *)          machine="UNKNOWN:${unameOut}"
esac

cd textworld/thirdparty/

# Install command line Inform 7
if [ ! -e I7_6M62_Linux_all.tar.gz ]; then
    echo "Downloading Inform7 CLI"
    curl -LO http://emshort.com/inform-app-archive/6M62/I7_6M62_Linux_all.tar.gz
    if [ "${machine}" == 'Mac' ] && [ ! -e I7-6M62-OSX-Interim.dmg ]; then
        echo "Downloading Inform7 for Mac"
        curl -LO http://emshort.com/inform-app-archive/6M62/I7-6M62-OSX-Interim.dmg
    fi
fi
if [ ! -d inform7-6M62 ]; then
    tar xf I7_6M62_Linux_all.tar.gz
fi
(
    echo "Installing Inform7 CLI"
    cd inform7-6M62/
    # Manually extract the files from the tarballs instead of calling install-inform7.sh.
    # ./install-inform7.sh --prefix $PWD
    tar xzf "inform7-common_6M62_all.tar.gz"
    if [ "${machine}" != 'Mac' ]; then
        ARCH=$(uname -m)
        tar xzf "inform7-compilers_6M62_${ARCH}.tar.gz"
        tar xzf "inform7-interpreters_6M62_${ARCH}.tar.gz"
    fi

    cd ..
    rm -f inform7-6M62/share/inform7/Internal/I6T/Actions.i6t
    cp inform7/share/inform7/Internal/I6T/Actions.i6t inform7-6M62/share/inform7/Internal/I6T/Actions.i6t
)

# Mount DMG if we're using a Mac
if [ "${machine}" == 'Mac' ] && [ -e inform7-6M62 ]; then
    echo "Mounting Inform for Mac"
    hdiutil attach ./I7-6M62-OSX-Interim.dmg

    echo "Copying Mac compiled inform files"
    current_dir="$(pwd)"
    cd /Volumes/Inform/Inform.app/Contents/MacOS
    mkdir -p "$current_dir/inform7-6M62/share/inform7/Compilers/"
    mkdir -p "$current_dir/inform7-6M62/share/inform7/Interpreters/"
    cp cBlorb inform6 Inform intest ni "$current_dir/inform7-6M62/share/inform7/Compilers/"
    cp ./git* "$current_dir/inform7-6M62/share/inform7/Interpreters/dumb-git"
    cp ./glulxe* "$current_dir/inform7-6M62/share/inform7/Interpreters/dumb-glulxe"

    cd "$current_dir"

    echo "Unmounting Inform for Mac"
    hdiutil detach /Volumes/Inform/
fi


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
