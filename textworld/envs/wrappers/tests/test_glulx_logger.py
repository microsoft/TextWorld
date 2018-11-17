# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import textworld
import numpy as np

from textworld.envs.wrappers import GlulxLogger
from textworld.utils import make_temp_directory
from textworld.generator import compile_game
from textworld import g_rng


def test_glulx_logger():
    num_nodes = 3
    num_items = 10
    g_rng.set_seed(1234)
    grammar_flags = {"theme": "house", "include_adj": True}
    game = textworld.generator.make_game(world_size=num_nodes, nb_objects=num_items, quest_length=3, grammar_flags=grammar_flags)

    game_name = "test_glulx_logger"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)

        env = textworld.start(game_file)
        env = GlulxLogger(env)
        env.activate_state_tracking()
        game_state = env.reset()
        game_state = env.reset()
        assert len(env.all_logs.logs) == 2

    # test reset
    assert 'state' in env.current

    # test step
    options = game_state.admissible_commands
    game_state, score, done = env.step(options[0])
    assert len(env.logs) > 1
    assert 'command' in env.current
    assert 'state' in env.current
    assert 'feedback' in env.current

    # test add_commands
    option_scores = np.array([0.1] * len(options))
    env.add_commands(options, option_scores)
    assert len(env.current['commands']) == len(env.current['command_scores'])

    # test add
    additional_info = {'scores': option_scores}
    env.add(additional_info)
    assert len(env.current['optional']) > 0



