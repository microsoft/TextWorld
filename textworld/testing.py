# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import sys
import contextlib


@contextlib.contextmanager
def capture_stdout():
    # Capture stdout.
    stdout_bak = sys.stdout
    sys.stdout = out = io.StringIO()
    try:
        yield out
    finally:
        # Restore stdout
        sys.stdout = stdout_bak
