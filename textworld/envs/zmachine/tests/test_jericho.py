# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest
from os.path import join as pjoin

import pytest
import jericho
import numpy as np

import textworld
from textworld import g_rng
from textworld import testing

from textworld.core import EnvInfos
from textworld.core import GameNotRunningError
from textworld.generator.maker import GameMaker
from textworld.utils import make_temp_directory

from textworld.envs.zmachine.jericho import JerichoEnv


def assert_jericho_state_equals(s1, s2):
    assert len(s1) == len(s2)
    for e1, e2 in zip(s1, s2):
        assert np.all(e1 == e2)


class TestJerichoEnv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = pjoin(cls.tmpdir, "tw-game.z8")
        cls.game, cls.game_file = testing.build_and_compile_game(cls.options)
        cls.request_infos = EnvInfos(
            max_score=True,
            score=True,
            won=True,
            lost=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = JerichoEnv(self.request_infos)
        self.env.load(self.game_file)
        self.game_state = self.env.reset()

    def tearDown(self):
        self.env.close()

    def test_feedback(self):
        # Check feedback for dropping and taking the carrot.
        game_state, _, _ = self.env.step("drop carrot")
        assert "drop the carrot on the ground" in game_state.feedback
        game_state, _, _ = self.env.step("take carrot")
        assert "pick up the carrot from the ground" in game_state.feedback

    def test_score(self):
        assert self.game_state.score == 0
        assert self.game_state.max_score == 3
        game_state, _, _ = self.env.step("go east")
        assert game_state.score == 0
        game_state, _, _ = self.env.step("insert carrot into chest")
        assert game_state.score == 2
        assert game_state.max_score == 3
        game_state, _, _ = self.env.step("close chest")
        assert game_state.score == 3

    def test_game_ended_when_no_quest(self):
        M = GameMaker()

        room = M.new_room()
        M.set_player(room)
        item = M.new(type="o")
        room.add(item)

        game = M.build()
        game_name = "test_game_ended_when_no_quest"
        with make_temp_directory(prefix=game_name) as tmpdir:
            options = textworld.GameOptions()
            options.path = pjoin(tmpdir, "tw-no_quest.z8")
            game_file = textworld.generator.compile_game(game, options)

            env = JerichoEnv(self.request_infos)
            env.load(game_file)
            game_state = env.reset()

            assert not game_state.lost
            assert not game_state.won
            game_state, _, _ = env.step("look")
            assert not game_state.lost
            assert not game_state.won

    def test_won(self):
        assert not self.game_state.won
        game_state, _, _ = self.env.step("go east")
        assert not game_state.won
        game_state, _, _ = self.env.step("insert carrot into chest")
        assert not game_state.won
        game_state, _, _ = self.env.step("close chest")
        assert game_state.won

    def test_lost(self):
        assert not self.game_state.lost
        game_state, _, _ = self.env.step("go east")
        assert not game_state.lost
        game_state, _, _ = self.env.step("eat carrot")
        assert game_state.lost

    def test_render(self):
        # Only validates that render does not raise exception.
        with testing.capture_stdout() as stdout:
            self.env.render()
            stdout.seek(0)
            assert len(stdout.read()) > 0

        assert self.env.render(mode="text").strip() == self.game_state.feedback.strip()

        # Try rendering to a file.
        f = self.env.render(mode="ansi")
        f.seek(0)
        assert f.read().strip() == self.game_state.feedback.strip()

        # Display command that was just entered.
        self.env.step("look")
        text1 = self.env.render(mode="text")
        self.env.display_command_during_render = True
        text2 = self.env.render(mode="text")
        assert "> look" not in text1
        assert "> look" in text2

    def test_step(self):
        env = JerichoEnv(self.request_infos)
        with pytest.raises(GameNotRunningError):
            env.step("look")

        with pytest.raises(GameNotRunningError):
            env.step("look")

        # Test sending empty command.
        self.env.reset()
        self.env.step("")

    def test_loading_unsupported_game(self):
        game_file = pjoin(self.tmpdir, "dummy.z8")
        shutil.copyfile(self.game_file, game_file)

        env = JerichoEnv(self.request_infos)

        with pytest.warns(jericho.UnsupportedGameWarning):
            env.load(game_file)

        game_state = env.reset()
        assert game_state.max_score is None

        for command in self.game.metadata["walkthrough"]:
            game_state, score, done = env.step(command)
            # Score is None and `done` is always False for unsupported games.
            assert score is None
            assert game_state.score is None
            assert done is False

        assert "The End" in game_state.feedback
        assert game_state.won is None
        assert game_state.lost is None

    def test_copy(self):
        env = JerichoEnv(self.request_infos)

        # Copy before env.reset.
        bkp = env.copy()
        assert bkp.gamefile == env.gamefile
        assert bkp._seed == env._seed
        assert bkp._jericho == env._jericho
        assert bkp.state == env.state
        assert bkp.request_infos == env.request_infos

        # Copy after env.reset.
        env.load(self.game_file)
        game_state = env.reset()
        bkp = env.copy()
        assert bkp.gamefile == env.gamefile
        assert bkp.request_infos == env.request_infos
        assert bkp._seed == env._seed
        assert bkp._jericho != env._jericho  # Not the same object.
        assert_jericho_state_equals(bkp._jericho.get_state(),
                                    env._jericho.get_state())  # But same state.
        assert bkp.state == env.state

        # Keep a copy of some information for later use.
        jericho_id = id(bkp._jericho)
        jericho_state = bkp._jericho.get_state()
        state = bkp.state.copy()

        # Check copy after a few env.step.
        walkthrough = self.game.metadata["walkthrough"]
        for command in walkthrough[:len(walkthrough) // 2]:
            game_state, score, done = env.step(command)

        # Check the copied env didn't change after calling env.step.
        assert id(bkp._jericho) == jericho_id
        assert_jericho_state_equals(bkp._jericho.get_state(), jericho_state)
        assert bkp.state == state

        # Bring the copied env up-to-date by issuing the same commands.
        walkthrough = self.game.metadata["walkthrough"]
        for command in walkthrough[:len(walkthrough) // 2]:
            game_state, score, done = bkp.step(command)

        # And compare the states.
        assert_jericho_state_equals(bkp._jericho.get_state(),
                                    env._jericho.get_state())

        bkp = env.copy()
        assert bkp._jericho != env._jericho  # Not the same object.
        assert_jericho_state_equals(bkp._jericho.get_state(),
                                    env._jericho.get_state())  # But same state.
        assert bkp.state == env.state

    def test_load(self):
        env = JerichoEnv(self.request_infos)

        env.load(self.game_file)
        env.reset()
        jericho_ref = id(env._jericho)

        env.load(self.game_file)
        env.reset()
        jericho_ref2 = id(env._jericho)
        assert jericho_ref == jericho_ref2
