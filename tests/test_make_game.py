# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld
from textworld import g_rng
from textworld.utils import make_temp_directory


def test_making_game_with_names_to_exclude():
    g_rng.set_seed(42)

    with make_temp_directory(prefix="test_render_wrapper") as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.nb_rooms = 2
        options.nb_objects = 20
        options.chaining.max_depth = 3
        options.chaining.max_breadth = 2
        options.seeds = 123
        game_file1, game1 = textworld.make(options)

        options2 = options.copy()
        game1_objects_names = [info.name for info in game1.infos.values() if info.name is not None]
        options2.grammar.names_to_exclude = game1_objects_names
        game_file2, game2 = textworld.make(options2)
        game2_objects_names = [info.name for info in game2.infos.values() if info.name is not None]
        assert len(set(game1_objects_names) & set(game2_objects_names)) == 0


def test_making_game_is_reproducible_with_seed():
    with make_temp_directory(prefix="test_render_wrapper") as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.nb_rooms = 2
        options.nb_objects = 20
        options.chaining.max_depth = 3
        options.chaining.max_breadth = 2
        options.seeds = 123

        game_file1, game1 = textworld.make(options)
        options2 = options.copy()
        game_file2, game2 = textworld.make(options2)
        assert game_file1 == game_file2
        assert game1 == game2
        # Make sure they are not the same Python objects.
        assert id(game1) != id(game2)
