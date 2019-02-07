#!/bin/bash

set -e

if ! grep 'vsyscall=emulate' /proc/cmdline >/dev/null; then
    cat >&2 <<EOF
WARNING: The manylinux Docker images require the host kernel to have vsyscall
emulation enabled, usually by adding vsyscall=emulate to the kernel command line
EOF
fi

python setup.py sdist

docker run --rm -v "$PWD":/usr/src/TextWorld quay.io/pypa/manylinux1_x86_64 /usr/src/TextWorld/package-impl.sh
