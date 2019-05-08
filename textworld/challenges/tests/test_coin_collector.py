# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import os
import glob
from subprocess import check_call
from os.path import join as pjoin

from numpy.testing import assert_raises

import textworld
import textworld.agents
import textworld.challenges
from textworld.challenges.coin_collector import make
from textworld.utils import make_temp_directory


def test_making_coin_collector():
    for level in [1, 100, 101]:
        options = textworld.GameOptions()
        options.seeds = 1234

        settings = {"level": level}
        game = make(settings, options)
        assert len(game.quests[0].commands) == (level - 1) % 100 + 1

    # Not enough variation for 200 rooms.
    options = textworld.GameOptions()
    options.seeds = 1234
    settings = {"level": 200}
    assert_raises(ValueError, make, settings, options)

    for level in [200, 201, 300]:
        print(level)
        options = textworld.GameOptions()
        options.seeds = 1234
        options.grammar.allowed_variables_numbering = True

        settings = {"level": level}
        game = make(settings, options)
        assert len(game.quests[0].commands) == (level - 1) % 100 + 1

