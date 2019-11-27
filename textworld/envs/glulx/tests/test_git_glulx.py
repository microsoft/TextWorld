# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import shutil
import tempfile
import unittest

import numpy.testing as npt

import textworld
from textworld import g_rng
from textworld import testing

from textworld.core import GameNotRunningError

from textworld.envs.glulx.git_glulx import GitGlulxEnv


class TestGitGlulxEnv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.tmpdir = tempfile.mkdtemp()
        cls.options = textworld.GameOptions()
        cls.options.path = cls.tmpdir
        cls.options.file_ext = ".ulx"
        cls.game, cls.game_file = testing.build_and_compile_game(cls.options)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = GitGlulxEnv()
        self.env.load(self.game_file)
        self.env.reset()

    def tearDown(self):
        self.env.close()

    def test_render(self):
        # Only validates that render does not raise exception.
        with testing.capture_stdout() as stdout:
            self.env.render()
            stdout.seek(0)
            assert len(stdout.read()) > 0

        assert self.env.render(mode="text").strip() == self.env.state.feedback.strip()

        # Try rendering to a file.
        f = self.env.render(mode="ansi")
        f.seek(0)
        assert f.read().strip() == self.env.state.feedback.strip()

        # Display command that was just entered.
        self.env.step("look")
        text1 = self.env.render(mode="text")
        self.env.display_command_during_render = True
        text2 = self.env.render(mode="text")
        assert "> look" not in text1
        assert "> look" in text2

    def test_step(self):
        env = GitGlulxEnv()
        npt.assert_raises(GameNotRunningError, env.step, "look")
        env.load(self.game_file)
        npt.assert_raises(GameNotRunningError, env.step, "look")

        # Test sending command when the game is done.
        self.env.reset()
        self.env.step("quit")
        self.env.step("yes")
        npt.assert_raises(GameNotRunningError, self.env.step, "look")

        # Test sending empty command.
        self.env.reset()
        self.env.step("")

    def test_quit_no(self):
        self.env.step("quit")
        self.env.step("no")
        self.env.step("look")
