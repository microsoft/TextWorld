# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import os
from os.path import join as pjoin
from subprocess import check_output

import textworld
from textworld.utils import make_temp_directory

SCRIPTS_PATH = os.path.abspath(pjoin(__file__, "..", "..", "scripts"))


def test_extract_vocab():
    script = pjoin(SCRIPTS_PATH, "extract_vocab.py")

    with make_temp_directory(prefix="test_extract_vocab") as tmpdir:
        outfile = pjoin(tmpdir, "vocab.txt")
        command = ["python", script, "house", "--output", outfile]
        stdout = check_output(command).decode()
        assert "Vocab size" in stdout
        assert os.path.isfile(outfile)
        nb_words = len(open(outfile).readlines())
        assert str(nb_words) in stdout
