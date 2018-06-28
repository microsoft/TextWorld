# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld
from textworld import g_rng
from textworld.utils import make_temp_directory


def test_making_game_with_names_to_exclude():
    g_rng.set_seed(42)

    with make_temp_directory(prefix="test_render_wrapper") as tmpdir:
        game_file1, game1 = textworld.make(2, 20, 3, {"names_to_exclude": []},
                                           seed=123, games_dir=tmpdir)

        game1_objects_names = [info.name for info in game1.infos.values() if info.name is not None]
        game_file2, game2 = textworld.make(2, 20, 3, {"names_to_exclude": game1_objects_names},
                                           seed=123, games_dir=tmpdir)
        game2_objects_names = [info.name for info in game2.infos.values() if info.name is not None]
        assert len(set(game1_objects_names) & set(game2_objects_names)) == 0


def test_making_game_is_reproducible_with_seed():
    grammar_flags = {}
    with make_temp_directory(prefix="test_render_wrapper") as tmpdir:
        game_file1, game1 = textworld.make(2, 20, 3, grammar_flags, seed=123, games_dir=tmpdir)
        game_file2, game2 = textworld.make(2, 20, 3, grammar_flags, seed=123, games_dir=tmpdir)
        assert game_file1 == game_file2
        assert game1 == game2
        # Make sure they are not the same Python objects.
        assert id(game1) != id(game2)
