# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest

import numpy as np

import textworld
import textworld.agents
from textworld.utils import make_temp_directory


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test_textworld")
        options = textworld.GameOptions()
        options.path = self.tmpdir
        options.nb_rooms = 5
        options.nb_objects = 10
        options.quest_length = 10
        options.seeds = 1234
        self.game_file, self.game = textworld.make(options)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_100_sequential_runs(self):
        for i in range(1, 100):
            env = textworld.start(self.game_file)
            env.reset()
            game_state, reward, done = env.step('take inventory')
            self.assertIsNotNone(game_state, "Checking gamestate is not None")
            self.assertIsNotNone(reward, "Checking reward is not None")
            self.assertFalse(done, "Checking we don't finish the game by looking at our stuff")

    def test_simultaneous_runs(self):
        envs = []
        for i in range(1, 100):
            env = textworld.start(self.game_file)
            env.reset()
            envs.append(env)

        game_state, reward, done = envs[-1].step('take inventory')
        self.assertIsNotNone(game_state, "Checking gamestate is not None")
        self.assertIsNotNone(reward, "Checking reward is not None")
        self.assertFalse(done, "Checking we don't finish the game by looking at our stuff")

    def test_game_random_agent(self):
        env = textworld.start(self.game_file)
        agent = textworld.agents.RandomCommandAgent()
        agent.reset(env)
        game_state = env.reset()

        reward = 0
        done = False
        for _ in range(5):
            command = agent.act(game_state, reward, done)
            game_state, reward, done = env.step(command)

    def test_game_walkthrough_agent(self):
        agent = textworld.agents.WalkthroughAgent()
        env = textworld.start(self.game_file)
        commands = self.game.main_quest.commands
        agent.reset(env)
        game_state = env.reset()

        reward = 0
        done = False
        for walkthrough_command in commands:
            self.assertFalse(done, 'walkthrough finished game too early')
            command = agent.act(game_state, reward, done)
            self.assertEqual(walkthrough_command, command, "Walkthrough agent issued unexpected command")
            game_state, reward, done = env.step(command)
        self.assertTrue(done, 'Walkthrough did not finish the game')


def test_playing_generated_games():
    NB_GAMES = 10
    rng = np.random.RandomState(1234)
    for i in range(NB_GAMES):

        # Sample game specs.
        world_size = rng.randint(1, 10)
        nb_objects = rng.randint(0, 20)
        quest_depth = rng.randint(2, 5)
        quest_breadth = rng.randint(3, 7)
        game_seed = rng.randint(0, 65365)

        with make_temp_directory(prefix="test_play_generated_games") as tmpdir:
            options = textworld.GameOptions()
            options.path = tmpdir
            options.nb_rooms = world_size
            options.nb_objects = nb_objects
            options.chaining.max_depth = quest_depth
            options.chaining.max_breadth = quest_breadth
            options.seeds = game_seed
            game_file, game = textworld.make(options)

            # Solve the game using WalkthroughAgent.
            agent = textworld.agents.WalkthroughAgent()
            textworld.play(game_file, agent=agent, silent=True)

            # Play the game using RandomAgent and make sure we can always finish the
            # game by following the winning policy.
            env = textworld.start(game_file)
            env.infos.policy_commands = True
            env.infos.game = True

            agent = textworld.agents.RandomCommandAgent()
            agent.reset(env)

            env.seed(4321)
            game_state = env.reset()

            max_steps = 100
            reward = 0
            done = False
            for step in range(max_steps):
                command = agent.act(game_state, reward, done)
                game_state, reward, done = env.step(command)

                if done:
                    assert game_state._winning_policy is None
                    game_state, reward, done = env.reset(), 0, False

                # Make sure the game can still be solved.
                winning_policy = game_state._winning_policy
                assert len(winning_policy) > 0
                assert game_state._game_progression.state.is_sequence_applicable(winning_policy)
