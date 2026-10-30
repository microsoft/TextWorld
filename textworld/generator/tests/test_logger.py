# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np

import textworld
from textworld.generator.logger import GameLogger


def test_logger():
    rng = np.random.RandomState(1234)
    game_logger = GameLogger()

    for _ in range(10):
        options = textworld.GameOptions()
        options.nb_rooms = 5
        options.nb_objects = 10
        options.chaining.max_depth = 3
        options.chaining.max_breadth = 3
        options.seeds = rng.randint(65635)

        game = textworld.generator.make_game(options)
        game_logger.collect(game)

    assert game_logger.stats().startswith("Nb. games: 10\n")
