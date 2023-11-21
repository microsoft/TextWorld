# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest
from os.path import join as pjoin

import numpy.testing as npt

import textworld
from textworld import g_rng
from textworld import testing

from textworld import EnvInfos
from textworld.envs import JerichoEnv, GitGlulxEnv
from textworld.envs.wrappers.tw_inform7 import TWInform7
from textworld.envs.wrappers.tw_inform7 import GameData, Inform7Data
from textworld.envs.wrappers.tw_inform7 import StateTracking
from textworld.envs.wrappers.tw_inform7 import MissingGameInfosError

from textworld.utils import make_temp_directory


class TestInform7Data(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = pjoin(cls.tmpdir, "tw-game.ulx")
        cls.game, cls.gamefile_ulx = testing.build_and_compile_game(cls.options)
        cls.options.path = pjoin(cls.tmpdir, "tw-game.z8")
        cls.gamefile_z8 = textworld.generator.compile_game(cls.game, cls.options)
        cls.request_infos = EnvInfos(
            inventory=True,
            description=True,
            score=True,
            moves=True,
            won=True,
            lost=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env_z8 = Inform7Data(JerichoEnv(self.request_infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = Inform7Data(GitGlulxEnv(self.request_infos))
        self.env_ulx.load(self.gamefile_ulx)

    def tearDown(self):
        self.env_z8.close()
        self.env_ulx.close()

    def test_description(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            game_state, _, _ = env.step("look")
            assert game_state.feedback.strip() == initial_state.description.strip()
            assert game_state.feedback.strip() == game_state.description.strip()
            game_state, _, _ = env.step("go east")
            game_state, _, _ = env.step("look")
            assert game_state.feedback.strip() == game_state.description.strip()
            previous_description = game_state.description
            game_state, _, _ = env.step("not a valid command")  # Description info should stay the same.
            assert game_state.description == previous_description

            # End the game.
            game_state, _, _ = env.step("insert carrot into chest")
            game_state, _, _ = env.step("close chest")
            assert game_state.description != ""

    def test_inventory(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            assert "carrot" in initial_state.inventory
            game_state, _, _ = env.step("inventory")
            assert game_state.feedback.strip() == initial_state.inventory.strip()
            previous_inventory = game_state.inventory
            game_state, _, _ = env.step("not a valid command")  # Inventory info should stay the same.
            assert game_state.inventory == previous_inventory
            game_state, _, _ = env.step("drop carrot")
            assert "nothing" in game_state.inventory, game_state.inventory

            # End the game.
            game_state, _, _ = env.step("take carrot")
            game_state, _, _ = env.step("go east")
            game_state, _, _ = env.step("insert carrot into chest")
            assert "carrying nothing" in game_state.inventory

            game_state, _, _ = env.step("close chest")
            assert game_state.inventory != ""  # Game has ended

    def test_score(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            assert initial_state.score == 0
            game_state, _, _ = env.step("go east")
            assert game_state.score == 0
            game_state, _, _ = env.step("insert carrot into chest")
            assert game_state.score == 2
            previous_score = game_state.score
            game_state, _, _ = env.step("not a valid command")  # Score info should stay the same.
            assert game_state.score == previous_score
            game_state, _, _ = env.step("close chest")
            assert game_state.score == 3

    def test_moves(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            assert initial_state.moves == 0
            game_state, _, _ = env.step("go east")
            assert game_state.moves == 1
            game_state, _, _ = env.step("insert carrot into chest")
            assert game_state.moves == 2
            previous_moves = game_state.moves
            game_state, _, _ = env.step("not a valid command")  # Moves info should stay the same.
            assert game_state.moves == previous_moves
            game_state, _, _ = env.step("close chest")
            assert game_state.moves == 3

    def test_won(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            assert not initial_state.won
            game_state, _, _ = env.step("go east")
            assert not game_state.won
            game_state, _, done = env.step("insert carrot into chest")
            assert not game_state.won
            assert not done
            game_state, _, done = env.step("close chest")
            assert game_state.won
            assert done

    def test_lost(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            assert not initial_state.lost
            game_state, _, _ = env.step("go east")
            assert not game_state.lost
            game_state, _, done = env.step("eat carrot")
            assert done
            assert game_state.lost

    def test_copy(self):
        npt.assert_raises(NotImplementedError, self.env_ulx.copy)

        # Copy before env.reset.
        env = self.env_z8.copy()
        assert env.state == self.env_z8.state
        assert env.request_infos == self.env_z8.request_infos
        assert env._tracked_infos == self.env_z8._tracked_infos
        assert env._prev_state == self.env_z8._prev_state

        # Copy after env.reset.
        self.env_z8.reset()
        env = self.env_z8.copy()
        assert sorted(env.state.items()) == sorted(self.env_z8.state.items())
        assert env.request_infos == self.env_z8.request_infos
        assert env._tracked_infos == self.env_z8._tracked_infos
        assert env._prev_state == self.env_z8._prev_state

        # Check copy after a few env.step.
        game_state, _, _ = self.env_z8.step("go east")
        assert env.state == self.env_z8._prev_state

        env = self.env_z8.copy()
        assert env._prev_state is not None
        prev_state = env._prev_state.copy()

        # Check the copied env didn't change after calling env.step.
        game_state, _, done = self.env_z8.step("eat carrot")
        assert env._prev_state == prev_state


class TestTWInform7(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = pjoin(cls.tmpdir, "tw-game.ulx")
        cls.game, cls.gamefile_ulx = testing.build_and_compile_game(cls.options)
        cls.options.path = pjoin(cls.tmpdir, "tw-game.z8")
        cls.gamefile_z8 = textworld.generator.compile_game(cls.game, cls.options)
        cls.request_infos = EnvInfos(
            inventory=True,
            description=True,
            score=True,
            moves=True,
            won=True,
            lost=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env_z8 = TWInform7(JerichoEnv(self.request_infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = TWInform7(GitGlulxEnv(self.request_infos))
        self.env_ulx.load(self.gamefile_ulx)

    def tearDown(self):
        self.env_z8.close()
        self.env_ulx.close()

    def test_compatible(self):
        assert TWInform7.compatible(self.gamefile_ulx)
        assert TWInform7.compatible(self.gamefile_z8)

        # To be compatible, a game needs the .json alongside its z8/ulx file.
        gamefile_json = self.gamefile_z8.replace(".z8", ".json")
        shutil.move(gamefile_json, gamefile_json + ".bkp")
        assert not TWInform7.compatible(self.gamefile_ulx)
        assert not TWInform7.compatible(self.gamefile_z8)
        shutil.move(gamefile_json + ".bkp", gamefile_json)

    def test_copy(self):
        npt.assert_raises(NotImplementedError, self.env_ulx.copy)

        # Copy before env.reset.
        env = self.env_z8.copy()
        assert env.state == self.env_z8.state
        assert env.request_infos == self.env_z8.request_infos
        assert env._tracked_infos == self.env_z8._tracked_infos
        assert env._prev_state == self.env_z8._prev_state

        # Copy after env.reset.
        self.env_z8.reset()
        env = self.env_z8.copy()
        assert sorted(env.state.items()) == sorted(self.env_z8.state.items())
        assert env.request_infos == self.env_z8.request_infos
        assert env._tracked_infos == self.env_z8._tracked_infos
        assert env._prev_state == self.env_z8._prev_state

        # Check copy after a few env.step.
        game_state, _, _ = self.env_z8.step("go east")
        assert env.state == self.env_z8._prev_state

        env = self.env_z8.copy()
        assert env._prev_state is not None
        prev_state = env._prev_state.copy()

        # Check the copied env didn't change after calling env.step.
        game_state, _, done = self.env_z8.step("eat carrot")
        assert env._prev_state == prev_state

    def test_no_quest_game(self):
        game_name = "tw-no_quest_game"
        with make_temp_directory(prefix=game_name) as tmpdir:
            for ext, env_class in [(".ulx", GitGlulxEnv), (".z8", JerichoEnv)]:
                options = textworld.GameOptions()
                options.path = pjoin(tmpdir, game_name + ext)

                game, gamefile = testing.build_and_compile_no_quest_game(options)

                env = TWInform7(env_class())
                env.load(gamefile)
                game_state = env.reset()

                assert not game_state.game_ended
                game_state, _, done = env.step("look")
                assert not done
                assert not game_state.game_ended


class TestGameData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = pjoin(cls.tmpdir, "tw-game.ulx")
        cls.game, cls.gamefile_ulx = testing.build_and_compile_game(cls.options)
        cls.options.path = pjoin(cls.tmpdir, "tw-game.z8")
        cls.gamefile_z8 = textworld.generator.compile_game(cls.game, cls.options)
        cls.request_infos = EnvInfos(
            max_score=True,
            objective=True,
            win_facts=True,
            fail_facts=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env_z8 = GameData(JerichoEnv(self.request_infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = GameData(GitGlulxEnv(self.request_infos))
        self.env_ulx.load(self.gamefile_ulx)

    def tearDown(self):
        self.env_z8.close()
        self.env_ulx.close()

    def test_max_score(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()
            assert initial_state.max_score == 3

    def test_objective(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()
            assert initial_state.objective.strip() in initial_state.feedback
            game_state, _, _ = env.step("goal")
            assert game_state.feedback.strip() == initial_state.objective

    def test_win_facts(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()
            assert len(initial_state.win_facts) == len(self.game.quests)
            for i, quest in enumerate(self.game.quests):
                assert len(initial_state.win_facts[i]) == len(quest.win_events)
                for j, event in enumerate(quest.win_events):
                    assert len(initial_state.win_facts[i][j]) == len(event.condition.preconditions)

            game_state, _, _ = env.step("look")
            assert game_state.win_facts == initial_state.win_facts

    def test_fail_facts(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()
            assert len(initial_state.fail_facts) == len(self.game.quests)
            for i, quest in enumerate(self.game.quests):
                assert len(initial_state.fail_facts[i]) == len(quest.fail_events)
                for j, event in enumerate(quest.fail_events):
                    assert len(initial_state.fail_facts[i][j]) == len(event.condition.preconditions)

            game_state, _, _ = env.step("look")
            assert game_state.fail_facts == initial_state.fail_facts

    def test_missing_game_infos_file(self):
        with make_temp_directory() as tmpdir:
            for ext, env_class in [(".ulx", GitGlulxEnv), (".z8", JerichoEnv)]:
                gamefile = pjoin(tmpdir, "tmp" + ext)
                with open(gamefile, "w"):
                    pass  # Empty file

                env = TWInform7(env_class())
                npt.assert_raises(MissingGameInfosError, env.load, gamefile)

    def test_copy(self):
        npt.assert_raises(NotImplementedError, self.env_ulx.copy)

        # Copy before env.reset.
        env = self.env_z8.copy()
        assert env._gamefile == self.env_z8._gamefile
        assert env._game == self.env_z8._game

        # Copy after env.reset.
        self.env_z8.reset()
        env = self.env_z8.copy()
        assert env._gamefile == self.env_z8._gamefile
        assert id(env._game) == id(self.env_z8._game)  # Reference


class TestStateTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = pjoin(cls.tmpdir, "tw-game.ulx")
        cls.game, cls.gamefile_ulx = testing.build_and_compile_game(cls.options)
        cls.options.path = pjoin(cls.tmpdir, "tw-game.z8")
        cls.gamefile_z8 = textworld.generator.compile_game(cls.game, cls.options)
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
        self.env_z8 = StateTracking(JerichoEnv(self.request_infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = StateTracking(GitGlulxEnv(self.request_infos))
        self.env_ulx.load(self.gamefile_ulx)

    def tearDown(self):
        self.env_z8.close()
        self.env_ulx.close()

    def test_intermediate_reward(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()

            assert initial_state.intermediate_reward == 0
            game_state, _, _ = env.step("drop carrot")
            assert game_state.intermediate_reward == -1
            game_state, _, _ = env.step("go west")
            assert game_state.intermediate_reward == 0
            game_state, _, _ = env.step("go east")
            game_state, _, _ = env.step("close chest")
            game_state, _, _ = env.step("go west")
            game_state, _, _ = env.step("take carrot")
            game_state, _, _ = env.step("go east")
            game_state, _, _ = env.step("open chest")
            game_state, _, _ = env.step("close wooden door")
            assert game_state.intermediate_reward == 0
            game_state, _, done = env.step("insert carrot into chest")
            game_state, _, done = env.step("close chest")
            assert done
            assert game_state.won
            assert game_state.intermediate_reward == 1

    def test_policy_commands(self):
        for env in [self.env_ulx, self.env_z8]:
            initial_state = env.reset()
            walkthrough = tuple(self.game.metadata["walkthrough"])

            assert tuple(initial_state.policy_commands) == walkthrough

            game_state, _, _ = env.step("drop carrot")
            assert tuple(game_state.policy_commands) == ("take carrot",) + walkthrough

            game_state, _, _ = env.step("take carrot")
            assert tuple(game_state.policy_commands) == walkthrough

            game_state, _, _ = env.step("go east")
            assert tuple(game_state.policy_commands) == walkthrough[1:]

            game_state, _, _ = env.step("insert carrot into chest")
            game_state, _, _ = env.step("close chest")
            assert game_state.policy_commands == [], game_state.policy_commands

            # Test parallel subquests.
            game_state = env.reset()
            walkthrough = list(walkthrough)
            assert game_state.policy_commands == walkthrough
            game_state, _, _ = env.step("close wooden door")
            assert game_state.policy_commands == ["open wooden door"] + walkthrough
            game_state, _, _ = env.step("drop carrot")
            is_policy1 = (game_state.policy_commands == ["take carrot", "open wooden door"] + walkthrough)
            is_policy2 = (game_state.policy_commands == ["open wooden door", "take carrot"] + walkthrough)
            assert is_policy1 or is_policy2, game_state.policy_commands
            game_state, _, _ = env.step("open wooden door")
            assert game_state.policy_commands == ["take carrot"] + walkthrough
            game_state, _, _ = env.step("go east")
            assert game_state.policy_commands == ["go west", "take carrot"] + walkthrough

            # Irreversible action.
            game_state = env.reset()
            assert tuple(game_state.policy_commands) == tuple(walkthrough)
            game_state, _, done = env.step("eat carrot")
            assert done
            assert game_state.lost
            assert len(game_state.policy_commands) == 0

    def test_admissible_commands(self):
        for env in [self.env_ulx, self.env_z8]:
            game_state = env.reset()
            # Make sure examine, look and inventory are in the admissible commands.
            assert "examine carrot" in game_state.admissible_commands
            assert "examine wooden door" in game_state.admissible_commands

            for command in self.game.metadata["walkthrough"]:
                assert "look" in game_state.admissible_commands
                assert "inventory" in game_state.admissible_commands
                assert command in game_state.admissible_commands
                game_state, _, done = env.step(command)

            assert done
            # Can't examine objects that are inside closed containers.
            assert "examine chest" in game_state.admissible_commands
            assert "examine carrot" not in game_state.admissible_commands

    def test_missing_game_infos_file(self):
        with make_temp_directory() as tmpdir:
            for ext, env_class in [(".ulx", GitGlulxEnv), (".z8", JerichoEnv)]:
                gamefile = pjoin(tmpdir, "tmp" + ext)
                with open(gamefile, "w"):
                    pass  # Empty file

                env = TWInform7(env_class())
                npt.assert_raises(MissingGameInfosError, env.load, gamefile)

    def test_copy(self):
        npt.assert_raises(NotImplementedError, self.env_ulx.copy)

        # Copy before env.reset.
        env = self.env_z8.copy()
        assert env._gamefile == self.env_z8._gamefile
        assert env._game == self.env_z8._game
        assert env._inform7 == self.env_z8._inform7
        assert env._last_action == self.env_z8._last_action
        assert env._previous_winning_policy == self.env_z8._previous_winning_policy
        assert env._current_winning_policy == self.env_z8._current_winning_policy
        assert env._moves == self.env_z8._moves
        assert env._game_progression == self.env_z8._game_progression

        # Copy after env.reset.
        self.env_z8.reset()
        env = self.env_z8.copy()
        assert env._gamefile == self.env_z8._gamefile
        assert id(env._game) == id(self.env_z8._game)  # Reference
        assert id(env._inform7) == id(self.env_z8._inform7)  # Reference
        assert env._last_action == self.env_z8._last_action
        assert env._previous_winning_policy == self.env_z8._previous_winning_policy
        assert tuple(env._current_winning_policy) == tuple(self.env_z8._current_winning_policy)
        assert env._moves == self.env_z8._moves
        assert id(env._game_progression) != id(self.env_z8._game_progression)
        assert env._game_progression.state == self.env_z8._game_progression.state

        # Keep a copy of some information for later use.
        current_winning_policy = list(env._current_winning_policy)
        game_progression = env._game_progression.copy()

        # Check copy after a few env.step.
        game_state, _, _ = self.env_z8.step("go east")
        assert env._game_progression.state != self.env_z8._game_progression.state
        game_state, _, done = self.env_z8.step("drop carrot")
        assert env._game_progression.state != self.env_z8._game_progression.state

        # Check the copied env didn't change after calling env.step.
        assert tuple(env._current_winning_policy) == tuple(current_winning_policy)
        assert tuple(env._current_winning_policy) != tuple(self.env_z8._current_winning_policy)
        assert env._game_progression.state == game_progression.state
