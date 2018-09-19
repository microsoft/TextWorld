# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np
from os.path import join as pjoin

import textworld
from textworld import g_rng
from textworld.utils import make_temp_directory
from textworld.generator.logger import GameLogger


def test_logger():
    rng = np.random.RandomState(1234)
    game_logger = GameLogger()

    for _ in range(10):
        seed = rng.randint(65635)
        g_rng.set_seed(seed)
        game = textworld.generator.make_game(world_size=5, nb_objects=10, quest_length=3, quest_breadth=3)
        game_logger.collect(game)

    with make_temp_directory(prefix="textworld_tests") as tests_folder:
        filename = pjoin(tests_folder, "game_logger.pkl")
        game_logger.save(filename)
        game_logger2 = GameLogger.load(filename)
        assert game_logger is not game_logger2
        assert game_logger.stats() == game_logger2.stats()
