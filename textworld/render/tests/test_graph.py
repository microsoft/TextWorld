# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import textworld
from textworld.utils import check_flag

from textworld.render import show_graph


def _make_game():
    options = textworld.GameOptions()
    options.seeds = 1234
    options.nb_rooms = 3
    options.nb_objects = 10
    options.quest_length = 3
    options.grammar.theme = "house"
    options.grammar.include_adj = True

    game = textworld.generator.make_game(options)
    return game


def test_show_graph():
    game = _make_game()

    renderer = None
    if check_flag("TEXTWORLD_DEBUG"):
        renderer = "browser"

    show_graph(game.world.facts, renderer=renderer)
