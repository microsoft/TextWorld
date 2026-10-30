import os
import builtins
import json
import shutil
import unittest
import tempfile
from os.path import join as pjoin
from unittest.mock import Mock

import pytest

from textworld import EnvInfos
from textworld.envs import PddlEnv
from textworld.envs.pddl.logic import GameLogic
from textworld.envs.pddl import textgen
from textworld.envs.pddl.textgen import CSGExpressionError


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


def _grammar_block(rules):
    return 'grammar :: """' + json.dumps(rules) + '""";'


@pytest.mark.parametrize("file_input", [False, True])
@pytest.mark.parametrize("location", ["intro", "unused", "action_local", "template", "feedback"])
def test_game_load_rejects_unsafe_expressions(location, file_input, tmp_path, monkeypatch):
    sentinel = Mock()
    monkeypatch.setattr(builtins, "grammar_sentinel", sentinel, raising=False)
    unsafe = "{grammar_sentinel()}"
    rules = {"intro": [{"rhs": "Welcome"}]}
    template, feedback, local_grammar = "review {o}", "#intro#", ""
    if location in ("intro", "unused"):
        rules[location] = [{"rhs": unsafe, "condition": "never(o:object)"}]
    elif location == "action_local":
        local_grammar = _grammar_block({"unused": [{"rhs": unsafe}]})
    elif location == "template":
        template = unsafe
    else:
        feedback = unsafe
    grammar = _grammar_block(rules) + (
        'action Review { template :: "' + template + '"; feedback :: "' + feedback + '"; ' + local_grammar + '}'
    )
    with open(pjoin(DATA_PATH, "domain.pddl")) as f:
        domain = f.read()
    with open(pjoin(DATA_PATH, "problem.pddl")) as f:
        problem = f.read()
    data = {"pddl_domain": domain, "pddl_problem": problem, "grammar": grammar}
    source = data
    if file_input:
        filename = tmp_path / "unsafe.tw-pddl"
        filename.write_text(json.dumps(data))
        source = str(filename)
    env = PddlEnv()
    try:
        with pytest.raises(CSGExpressionError, match="grammar_sentinel"):
            env.load(source)
    finally:
        env.close()
    sentinel.assert_not_called()


def test_validation_preserves_action_strings_and_late_bound_queries(monkeypatch):
    query = Mock(side_effect=AssertionError("Validation must not execute queries"))
    monkeypatch.setattr(textgen, "query", query)
    template = "review [{o.name | visible(o:object)}]"
    feedback = "{o.name or o.id}"
    grammar = _grammar_block({"intro": [{"rhs": "[{o.name | visible(o:object)}]"}]})
    grammar += 'action Review { template :: "' + template + '"; feedback :: "' + feedback + '"; }'
    logic = GameLogic("", grammar)
    assert logic.actions["review"].template == template
    assert logic.actions["review"].feedback_rule == feedback
    query.assert_not_called()
