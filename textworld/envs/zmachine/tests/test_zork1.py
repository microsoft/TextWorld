# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest
import urllib.request
from os.path import join as pjoin

import pytest

import textworld


ZORK1_URL = "https://archive.org/download/Zork1Release88Z-machineFile/zork1.z5"


@pytest.skip("Skipping Zork1 tests to avoid downloading from Internet.", allow_module_level=True)
class TestZork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.gamefile = pjoin(cls.tmpdir, "zork1.z5")
        urllib.request.urlretrieve(ZORK1_URL, cls.gamefile)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_losing_game(self):
        MAX_NB_STEPS = 1000  # Just in case.
        request_infos = textworld.EnvInfos(extras=["walkthrough"])
        env = textworld.start(self.gamefile, request_infos)
        agent = textworld.agents.WalkthroughAgent()
        agent.reset(env)

        env.seed(1234)  # In order for the walkthrough to lead to a death.
        game_state = env.reset()
        # env.render()

        done = False
        for t in range(MAX_NB_STEPS):
            command = agent.act(game_state, 0, done)
            game_state, reward, done = env.step(command)
            # env.render()

            if done:
                break

        print("Done after {} steps. Score {}/{}.".format(game_state.moves, game_state.score, game_state.max_score))
        assert game_state.lost
        assert not game_state.won

    def test_winning_game(self):
        MAX_NB_STEPS = 1000  # Just in case.
        request_infos = textworld.EnvInfos(extras=["walkthrough"])
        env = textworld.start(self.gamefile, request_infos)
        agent = textworld.agents.WalkthroughAgent()
        agent.reset(env)

        env.seed(12)  # In order for the walkthrough to work.
        game_state = env.reset()

        # env.render()

        done = False
        for t in range(MAX_NB_STEPS):
            command = agent.act(game_state, 0, done)
            game_state, reward, done = env.step(command)
            # env.render()

            if done:
                break

        print("Done after {} steps. Score {}/{}.".format(game_state.moves, game_state.score, game_state.max_score))
        assert game_state.won
        assert not game_state.lost
