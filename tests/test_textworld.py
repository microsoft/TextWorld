# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest

import textworld
import textworld.agents


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test_textworld")
        self.game_file, self.game = textworld.make(world_size=5, nb_objects=10,
                                                   quest_length=10, grammar_flags={},
                                                   seed=1234, games_dir=self.tmpdir)

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
        env.activate_state_tracking()
        commands = self.game.quests[-1].commands
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

