# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from subprocess import check_call

import textworld
from textworld.utils import make_temp_directory


def test_playing_a_game():
    for ext in [".z8"]:
        with make_temp_directory(prefix="test_tw-play") as tmpdir:
            options = textworld.GameOptions()
            options.file_ext = ext
            options.path = tmpdir
            options.nb_rooms = 5
            options.nb_objects = 10
            options.quest_length = 5
            options.quest_breadth = 2
            options.seeds = 1234
            game_file, _ = textworld.make(options)

            command = ["tw-play", "--max-steps", "100", "--mode", "random", game_file]
            assert check_call(command) == 0

            command = ["tw-play", "--max-steps", "100", "--mode", "random-cmd", game_file]
            assert check_call(command) == 0

            command = ["tw-play", "--max-steps", "100", "--mode", "walkthrough", game_file]
            assert check_call(command) == 0
