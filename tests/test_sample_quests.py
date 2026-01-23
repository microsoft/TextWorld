# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import os
from os.path import join as pjoin
from subprocess import check_output

from textworld.utils import make_temp_directory

SCRIPTS_PATH = os.path.abspath(pjoin(__file__, "..", "..", "scripts"))


def test_sample_quests():
    with make_temp_directory(prefix="test_sample_quests") as tmpdir:
        game_file = pjoin(tmpdir, "game.z8")
        command = ["tw-make", "custom", "--seed", "20181004", "--output", game_file]
        check_output(command).decode()

        script = pjoin(SCRIPTS_PATH, "sample_quests.py")
        command = ["python", script, "--nb-quests", "10", "--quest-length", "10",
                   "--quest-breadth", "5", "--output", tmpdir, game_file]
        stdout = check_output(command).decode()
        assert len(stdout) > 0
        assert os.path.isfile(pjoin(tmpdir, "sample_world.png"))
        assert os.path.isfile(pjoin(tmpdir, "sample_tree.svg"))
        assert os.path.isfile(pjoin(tmpdir, "sample_graph.svg"))
