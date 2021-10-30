# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld
from textworld.challenges import treasure_hunter


def test_making_treasure_hunter_games():
    for level in range(1, 30 + 1):
        options = textworld.GameOptions()
        options.seeds = 1234

        settings = {"level": level}
        game = treasure_hunter.make(settings, options)
        assert len(game.walkthrough) == game.metadata["quest_length"], "Level {}".format(level)
        assert len(game.world.rooms) == game.metadata["world_size"], "Level {}".format(level)
