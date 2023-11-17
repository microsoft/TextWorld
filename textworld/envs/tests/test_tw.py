# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest
from os.path import join as pjoin

import textworld
from textworld import g_rng
from textworld import testing

from textworld.core import EnvInfos

from textworld.envs.tw import TextWorldEnv
from textworld.envs.tw import DEFAULT_OBSERVATION


class TestTextWorldEnv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.gamefile = pjoin(cls.tmpdir, "tw-game.json")

        cls.game = testing.build_game(cls.options)
        cls.game.save(cls.gamefile)
        cls.request_infos = EnvInfos(
            facts=True,
            policy_commands=True,
            admissible_commands=True,
            intermediate_reward=True
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = TextWorldEnv(self.request_infos)
        self.env.load(self.gamefile)

    def test_feedback(self):
        game_state = self.env.reset()
        assert game_state.feedback == DEFAULT_OBSERVATION
        assert game_state.raw == DEFAULT_OBSERVATION

        # Check feedback for dropping and taking the carrot.
        game_state, _, _ = self.env.step("drop carrot")
        assert game_state.feedback == DEFAULT_OBSERVATION
        assert game_state.raw == DEFAULT_OBSERVATION

        game_state, _, _ = self.env.step("dummy")
        assert game_state.feedback == "Invalid command."

    def test_intermediate_reward(self):
        initial_state = self.env.reset()

        assert initial_state.intermediate_reward == 0
        game_state, _, _ = self.env.step("drop carrot")
        assert game_state.intermediate_reward == -1
        game_state, _, _ = self.env.step("go west")
        assert game_state.intermediate_reward == 0
        game_state, _, _ = self.env.step("go east")
        game_state, _, _ = self.env.step("close chest")
        game_state, _, _ = self.env.step("go west")
        game_state, _, _ = self.env.step("take carrot")
        game_state, _, _ = self.env.step("go east")
        game_state, _, _ = self.env.step("open chest")
        game_state, _, _ = self.env.step("close wooden door")
        assert game_state.intermediate_reward == 0
        game_state, _, done = self.env.step("insert carrot into chest")
        game_state, _, done = self.env.step("close chest")
        assert done
        assert game_state.won
        assert game_state.intermediate_reward == 1

    def test_policy_commands(self):
        initial_state = self.env.reset()
        walkthrough = tuple(self.game.metadata["walkthrough"])

        assert tuple(initial_state.policy_commands) == walkthrough

        game_state, _, _ = self.env.step("drop carrot")
        assert tuple(game_state.policy_commands) == ("take carrot",) + walkthrough

        game_state, _, _ = self.env.step("take carrot")
        assert tuple(game_state.policy_commands) == walkthrough

        game_state, _, _ = self.env.step("go east")
        assert tuple(game_state.policy_commands) == walkthrough[1:]

        game_state, _, _ = self.env.step("insert carrot into chest")
        game_state, _, _ = self.env.step("close chest")
        assert game_state.policy_commands == [], game_state.policy_commands

        # Test parallel subquests.
        game_state = self.env.reset()
        walkthrough = list(walkthrough)
        assert game_state.policy_commands == walkthrough
        game_state, _, _ = self.env.step("close wooden door")
        assert game_state.policy_commands == ["open wooden door"] + walkthrough
        game_state, _, _ = self.env.step("drop carrot")
        is_policy1 = (game_state.policy_commands == ["take carrot", "open wooden door"] + walkthrough)
        is_policy2 = (game_state.policy_commands == ["open wooden door", "take carrot"] + walkthrough)
        assert is_policy1 or is_policy2, game_state.policy_commands
        game_state, _, _ = self.env.step("open wooden door")
        assert game_state.policy_commands == ["take carrot"] + walkthrough
        game_state, _, _ = self.env.step("go east")
        assert game_state.policy_commands == ["go west", "take carrot"] + walkthrough

        # Irreversible action.
        game_state = self.env.reset()
        assert tuple(game_state.policy_commands) == tuple(walkthrough)
        game_state, _, done = self.env.step("eat carrot")
        assert done
        assert game_state.lost
        assert len(game_state.policy_commands) == 0

    def test_admissible_commands(self):
        game_state = self.env.reset()
        # Make sure examine, look and inventory are in the admissible commands.
        assert "examine carrot" in game_state.admissible_commands
        assert "examine wooden door" in game_state.admissible_commands

        for command in self.game.metadata["walkthrough"]:
            assert "look" in game_state.admissible_commands
            assert "inventory" in game_state.admissible_commands
            assert command in game_state.admissible_commands
            game_state, _, done = self.env.step(command)

        assert done
        # Can't examine objects that are inside closed containers.
        assert "examine chest" in game_state.admissible_commands
        assert "examine carrot" not in game_state.admissible_commands

    def test_copy(self):
        # Copy before env.reset.
        env = self.env.copy()
        assert env._gamefile == self.env._gamefile
        assert env._game == self.env._game
        assert env._inform7 == self.env._inform7
        assert env._last_action == self.env._last_action
        assert env._previous_winning_policy == self.env._previous_winning_policy
        assert env._current_winning_policy == self.env._current_winning_policy
        assert env._moves == self.env._moves
        assert env._game_progression == self.env._game_progression

        # Copy after env.reset.
        self.env.reset()
        env = self.env.copy()
        assert env._gamefile == self.env._gamefile
        assert id(env._game) == id(self.env._game)  # Reference
        assert id(env._inform7) == id(self.env._inform7)  # Reference
        assert env._last_action == self.env._last_action
        assert env._previous_winning_policy == self.env._previous_winning_policy
        assert tuple(env._current_winning_policy) == tuple(self.env._current_winning_policy)
        assert env._moves == self.env._moves
        assert id(env._game_progression) != id(self.env._game_progression)
        assert env._game_progression.state == self.env._game_progression.state

        # Keep a copy of some information for later use.
        current_winning_policy = list(env._current_winning_policy)
        game_progression = env._game_progression.copy()

        # Check copy after a few env.step.
        game_state, _, _ = self.env.step("go east")
        assert env._game_progression.state != self.env._game_progression.state
        game_state, _, done = self.env.step("drop carrot")
        assert env._game_progression.state != self.env._game_progression.state

        # Check the copied env didn't change after calling env.step.
        assert tuple(env._current_winning_policy) == tuple(current_winning_policy)
        assert tuple(env._current_winning_policy) != tuple(self.env._current_winning_policy)
        assert env._game_progression.state == game_progression.state
