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

from textworld.core import EnvInfos
from textworld.core import GameNotRunningError
from textworld.generator.maker import GameMaker
from textworld.utils import make_temp_directory

from textworld.envs.zmachine.jericho import JerichoEnv


class TestJerichoEnv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = pjoin(cls.tmpdir, "tw-game.z8")
        cls.game, cls.game_file = testing.build_and_compile_game(cls.options)
        cls.infos = EnvInfos(
            max_score=True,
            score=True,
            won=True,
            lost=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = JerichoEnv(self.infos)
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

            env = JerichoEnv(self.infos)
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
        env = JerichoEnv(self.infos)
        npt.assert_raises(GameNotRunningError, env.step, "look")
        env.load(self.game_file)
        npt.assert_raises(GameNotRunningError, env.step, "look")

        # Test sending empty command.
        self.env.reset()
        self.env.step("")

    def test_loading_unsupported_game(self):
        game_file = pjoin(self.tmpdir, "dummy.z8")
        shutil.copyfile(self.game_file, game_file)

        env = JerichoEnv(self.infos)
        env.load(game_file)
        game_state = env.reset()
        assert game_state.max_score is None

        for command in self.game.main_quest.commands:
            game_state, score, done = env.step(command)
            # Score is None and `done` is always False for unsupported games.
            assert score is None
            assert game_state.score is None
            assert done is False

        assert "The End" in game_state.feedback
        assert game_state.won is None
        assert game_state.lost is None
