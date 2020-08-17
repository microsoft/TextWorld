# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest

from textworld.core import EnvInfos, GameState


class TestEnvInfos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = [(slot, True) for slot in EnvInfos.__slots__ if slot != "extras"]
        cls.env_empty = EnvInfos()
        cls.env_half = EnvInfos(**dict(args[::2]), extras=["extra1"])
        cls.env_full = EnvInfos(**dict(args), extras=["extra1", "extra2"])

    def test_eq(self):
        assert self.env_empty != self.env_half
        assert self.env_empty != self.env_full
        assert self.env_half != self.env_full

    def test_copy(self):
        for env in [self.env_empty, self.env_half, self.env_full]:
            copy = env.copy()
            assert id(copy) != id(env)
            assert id(copy.extras) != id(env.extras)
            assert copy == env


class TestGameState(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.state = GameState()
        cls.state["field_str"] = "value1"
        cls.state["field_int"] = 42
        cls.state["field_float"] = 4.2
        cls.state["field_list"] = ["str", -1, True, 1.2]

    def test_copy(self):
        state = self.state.copy()
        assert id(state) != id(self.state)
        assert state == self.state

        # Make sure it's a deepcopy.
        assert id(state["field_list"]) != id(self.state["field_list"])
