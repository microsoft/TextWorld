import os
import json
import shutil
import unittest
import tempfile
from os.path import join as pjoin

from textworld import EnvInfos
from textworld.envs import PddlEnv


DATA_PATH = os.path.abspath(pjoin(__file__, ".."))


class TestInterface(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.domain = open(pjoin(DATA_PATH, "domain.pddl")).read()
        cls.problem = open(pjoin(DATA_PATH, "problem.pddl")).read()
        cls.grammar = open(pjoin(DATA_PATH, "grammar.twl2")).read()

        cls.tmpdir = tempfile.mkdtemp()
        cls.gamefile = pjoin(cls.tmpdir, "tw-game.tw-pddl")

        cls.gamedata = {
            "pddl_domain": cls.domain,
            "pddl_problem": cls.problem,
            "grammar": cls.grammar,
        }
        json.dump(cls.gamedata, open(cls.gamefile, "w"))

        cls.request_infos = EnvInfos(
            facts=True,
            moves=True,
            policy_commands=True,
            admissible_commands=True,
            extras=["walkthrough"],
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = PddlEnv(self.request_infos)
        self.env.load(self.gamefile)

    def test_playing_pddl_game(self):
        game_state = self.env.reset()
        assert game_state.feedback.startswith("-= Welcome to TextWorld, ALFRED! =-")

        policy = game_state["policy_commands"]
        assert policy == game_state["extra.walkthrough"]

        reward, done = 0, False
        for cmd in policy:
            assert not done
            assert reward == 0
            game_state, reward, done = self.env.step(cmd)

        assert done
        assert reward == 1

        # Reset games and check that we can play it again.
        game_state = self.env.reset()
        assert game_state.feedback.startswith("-= Welcome to TextWorld, ALFRED! =-")

        # Try invalid commands.
        game_state, _, _ = self.env.step("dummy")
        assert game_state.feedback == "Nothing happens."

    def test_loading_from_data(self):
        env = PddlEnv(self.request_infos)
        env.load(self.gamedata)
        assert env._game_data == self.gamedata

        game_state = self.env.reset()
        assert game_state.feedback.startswith("-= Welcome to TextWorld, ALFRED! =-")
