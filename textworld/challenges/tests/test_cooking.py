# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import numpy as np

import textworld
from textworld.core import EnvInfos
from textworld.utils import make_temp_directory
from textworld.challenges import cooking


NB_TRIALS = 10


def test_making_cooking_games():
    options = textworld.GameOptions()
    options.seeds = 1234
    options.file_ext = ".z8"

    nb_ingredients = 2

    settings = {
        "recipe": nb_ingredients,
        "take": 3,
        "open": True,
        "open": True,
        "cook": True,
        "cut": False,
        "drop": False,
        "go": 12,
        "recipe_seed": 123,
        "split": "valid"
    }

    game = cooking.make(settings, options)
    assert len(game.metadata["ingredients"]) == nb_ingredients

    # Change only the recipe.
    options = textworld.GameOptions()
    options.seeds = 1234
    options.file_ext = ".z8"
    settings["recipe_seed"] = 321
    game2 = cooking.make(settings, options)

    # Recipe's ingredients should be different.
    assert game.metadata["ingredients"] != game2.metadata["ingredients"]
    assert game.metadata["entities"] == game2.metadata["entities"]

    # The rest of the world should stay the same.
    POSITIONNING_FACTS = ("in", "on", "at", "west_of", "east_of", "south_of", "north_of")
    differing_facts = set(game.world.facts) - set(game2.world.facts)
    assert [pred for pred in differing_facts if pred.name in POSITIONNING_FACTS] == []

    # Check the game can be completed by following the walkthrough.
    with make_temp_directory() as tmpdir:
        options.path = tmpdir
        game_file = textworld.generator.compile_game(game, options)
        infos = EnvInfos(admissible_commands=True, policy_commands=True)

        # agent = textworld.agents.WalkthroughAgent()
        # env = textworld.start(game_file, infos)
        # agent.reset(env)
        # game_state = env.reset()

        # reward = 0
        # done = False
        # while not done:
        #     command = agent.act(game_state, reward, done)
        #     assert command in game_state.admissible_commands, "Missing command {}".format(command)
        #     game_state, reward, done = env.step(command)

        # assert done
        # assert game_state["won"]

        def _assert_still_finishable(env, command):
            env = env.copy()
            game_state, _, done = env.step(command)

            if not game_state["policy_commands"]:
                assert game_state.lost
                return

            while not done:
                command = game_state["policy_commands"][0]
                game_state, _, done = env.step(command)

            assert game_state.won

        # Check the game can be completed by following the policy commands.
        env = textworld.start(game_file, infos)

        game_state = env.reset()

        rng = np.random.RandomState(20210510)
        done = False
        while not done:
            # Take a random action.
            random_command = rng.choice(game_state["admissible_commands"])
            _assert_still_finishable(env, random_command)

            # Resume winning policy.
            command = game_state["policy_commands"][0]
            game_state, _, done = env.step(command)

        assert game_state.won
