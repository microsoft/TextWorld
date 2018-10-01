# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from subprocess import check_call

import textworld
from textworld.utils import make_temp_directory


def test_playing_a_game():
    with make_temp_directory(prefix="test_tw-play") as tmpdir:
        game_file, _ = textworld.make(5, 10, 5, 4, {}, seed=1234, games_dir=tmpdir)

        command = ["tw-play", "--max-steps", "100", "--mode", "random", game_file]
        assert check_call(command) == 0

        command = ["tw-play", "--max-steps", "100", "--mode", "random-cmd", game_file]
        assert check_call(command) == 0

        command = ["tw-play", "--max-steps", "100", "--mode", "walkthrough", game_file]
        assert check_call(command) == 0