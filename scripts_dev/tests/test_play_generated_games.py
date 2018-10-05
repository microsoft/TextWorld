# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import os
from os.path import join as pjoin
from subprocess import check_output

import textworld
from textworld.utils import make_temp_directory

SCRIPTS_DEV_PATH = os.path.abspath(pjoin(__file__, "..", ".."))


def test_playing_generated_game():
    with make_temp_directory(prefix="test_play_generated_games") as tmpdir:
        script = pjoin(SCRIPTS_DEV_PATH, "play_generated_games.py")
        common_args = ["python", script, "--nb-games", "3", "--max-steps", "100", "--output", tmpdir]

        command = common_args + ["--mode", "walkthrough"]
        stdout = check_output(command).decode()
        assert tmpdir in stdout
        assert "Score 1/1" in stdout

        command = common_args + ["--mode", "random-cmd"]
        stdout = check_output(command).decode()
        assert tmpdir in stdout

        command = common_args + ["--mode", "random"]
        stdout = check_output(command).decode()
        assert tmpdir in stdout
