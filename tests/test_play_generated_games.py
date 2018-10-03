# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np

import textworld
from textworld.utils import make_temp_directory


def test_play_generated_games():
    NB_GAMES = 10
    rng = np.random.RandomState(1234)
    for i in range(NB_GAMES):

        # Sample game specs.
        world_size = rng.randint(1, 10)
        nb_objects = rng.randint(0, 20)
        quest_length = rng.randint(2, 5)
        quest_breadth = rng.randint(3, 7)
        game_seed = rng.randint(0, 65365)

        with make_temp_directory(prefix="test_play_generated_games") as tmpdir:
            options = textworld.GameOptions()
            options.nb_rooms = world_size
            options.nb_objects = nb_objects
            options.quest_length = quest_length
            options.quest_breadth = quest_breadth
            options.seeds = game_seed
            game_file, game = textworld.make(options, path=tmpdir)

            # Solve the game using WalkthroughAgent.
            agent = textworld.agents.WalkthroughAgent()
            textworld.play(game_file, agent=agent, silent=True)

            # Play the game using RandomAgent and make sure we can always finish the
            # game by following the winning policy.
            env = textworld.start(game_file)

            agent = textworld.agents.RandomCommandAgent()
            agent.reset(env)
            env.compute_intermediate_reward()

            env.seed(4321)
            game_state = env.reset()

            max_steps = 100
            reward = 0
            done = False
            for step in range(max_steps):
                command = agent.act(game_state, reward, done)
                game_state, reward, done = env.step(command)

                if done:
                    msg = "Finished before playing `max_steps` steps because of command '{}'.".format(command)
                    if game_state.has_won:
                        msg += " (winning)"
                        assert len(game_state._game_progression.winning_policy) == 0

                    if game_state.has_lost:
                        msg += " (losing)"
                        assert game_state._game_progression.winning_policy is None

                    print(msg)
                    break

                # Make sure the game can still be solved.
                winning_policy = game_state._game_progression.winning_policy
                assert len(winning_policy) > 0
                assert game_state.state.is_sequence_applicable(winning_policy)
