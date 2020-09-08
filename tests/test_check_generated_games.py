# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import os
from os.path import join as pjoin
from subprocess import check_output

from textworld.utils import make_temp_directory

SCRIPTS_PATH = os.path.abspath(pjoin(__file__, "..", "..", "scripts"))


def test_check_generated_game():
    NB_GAMES = 3
    script = pjoin(SCRIPTS_PATH, "check_generated_games.py")
    with make_temp_directory(prefix="test_check_generated_game") as tmpdir:
        for i in range(NB_GAMES):
            command = ["tw-make", "custom", "--seed", str(i), "--output", tmpdir]
            check_output(command).decode()

        game_files = [pjoin(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith(".z8")]
        assert len(game_files) == NB_GAMES
        command = ["python", script] + game_files
        stdout = check_output(command).decode()
        for file in game_files:
            assert "Testing " + file in stdout
