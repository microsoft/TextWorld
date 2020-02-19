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

python setup.py sdist

# Move back the Inform7 related files.
mv /tmp/tw_release_bkp/I7* /tmp/tw_release_bkp/inform7-6M62 textworld/thirdparty/

docker run --dns 1.1.1.1 --rm -v "$PWD":/usr/src/TextWorld quay.io/pypa/manylinux1_x86_64 /usr/src/TextWorld/tools/package-impl.sh
