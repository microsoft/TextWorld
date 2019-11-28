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
        cls.infos = EnvInfos(
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
        self.env_z8 = Inform7Data(JerichoEnv(self.infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = Inform7Data(GitGlulxEnv(self.infos))
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
            game_state, _, _ = env.step("close chest")
            assert game_state.score == 3

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


class TestTWInform7(unittest.TestCase):

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
        cls.infos = EnvInfos(
            max_score=True,
            objective=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env_z8 = GameData(JerichoEnv(self.infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = GameData(GitGlulxEnv(self.infos))
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

    def test_missing_game_infos_file(self):
        with make_temp_directory() as tmpdir:
            for ext, env_class in [(".ulx", GitGlulxEnv), (".z8", JerichoEnv)]:
                gamefile = pjoin(tmpdir, "tmp" + ext)
                with open(gamefile, "w"):
                    pass  # Empty file

                env = TWInform7(env_class())
                npt.assert_raises(MissingGameInfosError, env.load, gamefile)


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
        cls.infos = EnvInfos(
            facts=True,
            policy_commands=True,
            admissible_commands=True,
            intermediate_reward=True
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env_z8 = StateTracking(JerichoEnv(self.infos))
        self.env_z8.load(self.gamefile_z8)

        self.env_ulx = StateTracking(GitGlulxEnv(self.infos))
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

            assert tuple(initial_state.policy_commands) == self.game.main_quest.commands

            game_state, _, _ = env.step("drop carrot")
            expected = ("take carrot",) + self.game.main_quest.commands
            assert tuple(game_state.policy_commands) == expected, game_state.policy_commands

            game_state, _, _ = env.step("take carrot")
            expected = self.game.main_quest.commands
            assert tuple(game_state.policy_commands) == expected

            game_state, _, _ = env.step("go east")
            expected = self.game.main_quest.commands[1:]
            assert tuple(game_state.policy_commands) == expected

            game_state, _, _ = env.step("insert carrot into chest")
            game_state, _, _ = env.step("close chest")
            assert game_state.policy_commands == [], game_state.policy_commands

            # Test parallel subquests.
            game_state = env.reset()
            commands = list(self.game.main_quest.commands)
            assert game_state.policy_commands == commands
            game_state, _, _ = env.step("close wooden door")
            assert game_state.policy_commands == ["open wooden door"] + commands
            game_state, _, _ = env.step("drop carrot")
            is_policy1 = (game_state.policy_commands == ["take carrot", "open wooden door"] + commands)
            is_policy2 = (game_state.policy_commands == ["open wooden door", "take carrot"] + commands)
            assert is_policy1 or is_policy2, game_state.policy_commands
            game_state, _, _ = env.step("open wooden door")
            assert game_state.policy_commands == ["take carrot"] + commands
            game_state, _, _ = env.step("go east")
            assert game_state.policy_commands == ["go west", "take carrot"] + commands

            # Irreversible action.
            game_state = env.reset()
            assert tuple(game_state.policy_commands) == self.game.main_quest.commands
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

            for command in self.game.main_quest.commands:
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
