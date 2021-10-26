#!/bin/bash

set -e

if ! grep 'vsyscall=emulate' /proc/cmdline >/dev/null; then
    cat >&2 <<EOF
WARNING: The manylinux Docker images require the host kernel to have vsyscall
emulation enabled, usually by adding vsyscall=emulate to the kernel command line
EOF
fi

./tools/prep-release.sh

# Set up all the third-party dependencies
./setup.sh

# But don't include too much in the source package
# Temporarily move files related Inform7.
#rm -rf textworld/thirdparty/I7* textworld/thirdparty/inform7-6M62
mkdir -p /tmp/tw_release_bkp
mv textworld/thirdparty/I7* textworld/thirdparty/inform7-6M62 /tmp/tw_release_bkp/
make -C textworld/thirdparty/glulx/Git-Glulx clean
make -C textworld/thirdparty/glulx/cheapglk clean
rm -rf build *.egg-info

# Check if we are doing a prerelease.
if [[ ! -z $TEXTWORLD_PRERELEASE ]]; then
    cp textworld/version.py /tmp/tw_release_bkp/
    echo "__version__ = '`sed -r "s/[^']*'(.*)'/\1/" textworld/version.py | tail -n 1`'" > textworld/version.py
fi

python setup.py sdist

# Move back the Inform7 related files.
mv /tmp/tw_release_bkp/I7* /tmp/tw_release_bkp/inform7-6M62 textworld/thirdparty/

docker run --dns 1.1.1.1 --rm -v "$PWD":/usr/src/TextWorld quay.io/pypa/manylinux_2_24_x86_64 /usr/src/TextWorld/tools/package-impl.sh

echo -e "\e[33mTo upload, run the following:\e[0m"
echo -e "\e[33mpython -m twine upload dist/textworld-`sed -r "s/[^']*'(.*)'/\1/" textworld/version.py | head -n 1`*\e[0m"

# Move back original version file.
if [[ ! -z $TEXTWORLD_PRERELEASE ]]; then
    mv /tmp/tw_release_bkp/version.py textworld/
fi

