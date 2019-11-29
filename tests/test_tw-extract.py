# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import re
import os
from os.path import join as pjoin
from subprocess import check_output

import textworld
from textworld.utils import make_temp_directory


def test_extract_vocab():
    with make_temp_directory(prefix="test_extract_vocab") as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.nb_rooms = 5
        options.nb_objects = 10
        options.quest_length = 5
        options.quest_breadth = 2
        options.seeds = 1234
        game_file1, _ = textworld.make(options)
        options.seeds = 12345
        game_file2, _ = textworld.make(options)

        outfile = pjoin(tmpdir, "vocab.txt")
        command = ["tw-extract", "vocab", game_file1, game_file2, "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        nb_words = len(open(outfile).readlines())
        assert "Found {}".format(nb_words) in stdout


def test_extract_vocab_theme():
    with make_temp_directory(prefix="test_extract_vocab_theme") as tmpdir:
        outfile = pjoin(tmpdir, "vocab.txt")
        command = ["tw-extract", "vocab", "--theme", "house", "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        assert int(re.findall(r"Found (\d+)", stdout)[0]) > 0


def test_extract_entities():
    with make_temp_directory(prefix="test_extract_entities") as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.nb_rooms = 5
        options.nb_objects = 10
        options.quest_length = 5
        options.quest_breadth = 2
        options.seeds = 1234
        game_file, _ = textworld.make(options)

        outfile = pjoin(tmpdir, "entities.txt")
        command = ["tw-extract", "entities", game_file, "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        nb_entities = len(open(outfile).readlines())
        assert "Found {}".format(nb_entities) in stdout
