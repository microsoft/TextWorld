# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import pickle
import shutil
import tempfile
import unittest
from os.path import join as pjoin

import numpy as np
import numpy.testing as npt

import textworld
from textworld import g_rng
from textworld import testing

from textworld.generator.maker import GameMaker
from textworld.utils import make_temp_directory
from textworld.generator import data
from textworld.generator.game import Quest, Event
from textworld.generator.graph_networks import DIRECTIONS
from textworld.envs.glulx.git_glulx_ml import ExtraInfosIsMissingError
from textworld.envs.glulx.git_glulx_ml import StateTrackingIsRequiredError
from textworld.envs.glulx.git_glulx_ml import OraclePolicyIsRequiredError
from textworld.envs.glulx.git_glulx_ml import MissingGameInfosError
from textworld.envs.glulx.git_glulx_ml import GameNotRunningError


def build_test_game():
    M = GameMaker()

    # Create a 'bedroom' room.
    R1 = M.new_room("bedroom")
    R2 = M.new_room("kitchen")
    M.set_player(R1)

    path = M.connect(R1.east, R2.west)
    path.door = M.new(type='d', name='wooden door')
    path.door.add_property("open")

    carrot = M.new(type='f', name='carrot')
    M.inventory.add(carrot)

    # Add a closed chest in R2.
    chest = M.new(type='c', name='chest')
    chest.add_property("open")
    R2.add(chest)

    commands = ["go east", "insert carrot into chest"]
    quest1 = M.new_quest_using_commands(commands)
    quest1.reward = 2
    commands = ["go east", "insert carrot into chest", "close chest"]
    event = M.new_event_using_commands(commands)
    quest2 = Quest(win_events=[event])
    M.quests = [quest1, quest2]
    game = M.build()
    return game


def _compile_game(game, folder):
    grammar_flags = {
        "theme": "house",
        "include_adj": False,
        "only_last_action": True,
        "blend_instructions": True,
        "blend_descriptions": True,
        "refer_by_name_only": True,
        "instruction_extension": []
    }
    rng_grammar = np.random.RandomState(1234)
    grammar = textworld.generator.make_grammar(grammar_flags, rng=rng_grammar)
    game.change_grammar(grammar)

    game_name = "test_game"
    options = textworld.GameOptions()
    options.path = pjoin(folder, game_name + ".ulx")
    game_file = textworld.generator.compile_game(game, options)
    return game_file


class TestGlulxGameState(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        g_rng.set_seed(201809)
        cls.game = build_test_game()
        cls.tmpdir = tempfile.mkdtemp()
        cls.game_file = _compile_game(cls.game, folder=cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = textworld.start(self.game_file)
        self.env.activate_state_tracking()
        self.env.compute_intermediate_reward()
        self.env.enable_extra_info("description")
        self.env.enable_extra_info("inventory")
        self.game_state = self.env.reset()

    def tearDown(self):
        self.env.close()

    def test_feedback(self):
        # Initial feedback should contain the objective.
        assert self.game_state.objective in self.game_state.feedback
        game_state, _, _ = self.env.step("look")
        assert game_state.feedback == self.game_state.description

        # Check feedback for dropping and taking the carrot.
        game_state, _, _ = self.env.step("drop carrot")
        assert "drop the carrot on the ground" in game_state.feedback
        game_state, _, _ = self.env.step("take carrot")
        assert "pick up the carrot from the ground" in game_state.feedback

    def test_command_feedback(self):
        assert self.game_state.command_feedback.strip() == ""
        game_state, _, _ = self.env.step("look")
        assert game_state.command_feedback == ""
        game_state, _, _ = self.env.step("inv")
        assert game_state.command_feedback == ""

        # Check command feedback for dropping and taking the carrot.
        game_state, _, _ = self.env.step("drop carrot")
        assert "drop the carrot on the ground" in game_state.command_feedback
        game_state, _, _ = self.env.step("take carrot")
        assert "pick up the carrot from the ground" in game_state.command_feedback

    def test_inventory(self):
        assert "carrot" in self.game_state.inventory
        game_state, _, _ = self.env.step("inventory")
        assert game_state.feedback == self.game_state.inventory
        game_state, _, _ = self.env.step("drop carrot")
        assert "nothing" in game_state.inventory, game_state.inventory

        # End the game.
        game_state, _, _ = self.env.step("take carrot")
        game_state, _, _ = self.env.step("go east")
        game_state, _, _ = self.env.step("insert carrot into chest")
        assert "carrying nothing" in game_state.inventory

        game_state, _, _ = self.env.step("close chest")
        assert game_state.inventory != ""  # Game has ended

    def test_objective(self):
        assert self.game_state.objective.strip() in self.game_state.feedback
        game_state, _, _ = self.env.step("goal")
        assert game_state.feedback.strip() == self.game_state.objective

    def test_description(self):
        env = textworld.start(self.game_file)
        game_state = env.reset()
        npt.assert_raises(ExtraInfosIsMissingError, getattr, game_state, "description")

        game_state, _, _ = self.env.step("look")
        assert game_state.feedback.strip() == self.game_state.description.strip()
        assert game_state.feedback.strip() == game_state.description.strip()
        game_state, _, _ = self.env.step("go east")
        game_state, _, _ = self.env.step("look")
        assert game_state.feedback.strip() == game_state.description.strip()

        # End the game.
        game_state, _, _ = self.env.step("insert carrot into chest")
        game_state, _, _ = self.env.step("close chest")
        assert game_state.description != ""

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
            options.path = tmpdir
            game_file = textworld.generator.compile_game(game, options)

            env = textworld.start(game_file)
            env.activate_state_tracking()
            env.compute_intermediate_reward()
            game_state = env.reset()

            assert not game_state.game_ended
            game_state, _, done = env.step("look")
            assert not done
            assert not game_state.game_ended

    def test_has_won(self):
        assert not self.game_state.has_won
        game_state, _, _ = self.env.step("go east")
        assert not game_state.has_won
        game_state, _, done = self.env.step("insert carrot into chest")
        assert not game_state.has_won
        game_state, _, done = self.env.step("close chest")
        assert game_state.has_won

    def test_has_lost(self):
        assert not self.game_state.has_lost
        game_state, _, _ = self.env.step("go east")
        assert not game_state.has_lost
        game_state, _, done = self.env.step("eat carrot")
        assert done
        assert game_state.intermediate_reward == -1
        assert game_state.has_lost

    def test_intermediate_reward(self):
        assert self.game_state.intermediate_reward == 0
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
        assert game_state.has_won
        assert game_state.intermediate_reward == 1

    def test_policy_commands(self):
        assert self.game_state.policy_commands == self.game.main_quest.commands

        game_state, _, _ = self.env.step("drop carrot")
        expected = ["take carrot"] + self.game.main_quest.commands
        assert game_state.policy_commands == expected, game_state.policy_commands

        game_state, _, _ = self.env.step("take carrot")
        expected = self.game.main_quest.commands
        assert game_state.policy_commands == expected

        game_state, _, _ = self.env.step("go east")
        expected = self.game.main_quest.commands[1:]
        assert game_state.policy_commands == expected

        game_state, _, _ = self.env.step("insert carrot into chest")
        game_state, _, _ = self.env.step("close chest")
        assert game_state.policy_commands == [], game_state.policy_commands

        # Test parallel subquests.
        game_state = self.env.reset()
        commands = self.game.main_quest.commands
        assert game_state.policy_commands == commands
        game_state, _, _ = self.env.step("close wooden door")
        assert game_state.policy_commands == ["open wooden door"] + commands
        game_state, _, _ = self.env.step("drop carrot")
        assert (game_state.policy_commands == ["take carrot", "open wooden door"] + commands or
                game_state.policy_commands == ["open wooden door", "take carrot"] + commands), game_state.policy_commands
        game_state, _, _ = self.env.step("open wooden door")
        assert game_state.policy_commands == ["take carrot"] + commands
        game_state, _, _ = self.env.step("go east")
        assert game_state.policy_commands == ["go west", "take carrot"] + commands

        # Irreversible action.
        game_state = self.env.reset()
        assert game_state.policy_commands == self.game.main_quest.commands
        game_state, _, done = self.env.step("eat carrot")
        assert done
        assert game_state.has_lost
        assert len(game_state.policy_commands) == 0

    def test_admissible_commands(self):
        game_state = self.env.reset()
        # Make sure examine, look and inventory are in the admissible commands.
        assert "examine carrot" in game_state.admissible_commands
        assert "examine wooden door" in game_state.admissible_commands

        for command in self.game.main_quest.commands:
            assert "look" in game_state.admissible_commands
            assert "inventory" in game_state.admissible_commands
            assert command in game_state.admissible_commands
            game_state, _, done = self.env.step(command)

        assert done
        # Can't examine objects that are inside closed containers.
        assert "examine chest" in game_state.admissible_commands
        assert "examine carrot" not in game_state.admissible_commands

    def test_view(self):
        view = self.game_state.view()
        # Test that the view on the game_state is pickable.
        pickle.dumps(view)
        npt.assert_raises(TypeError, pickle.dumps, self.game_state)

        # Test properties are still accessible.
        props = ["description", "feedback", "command_feedback", "inventory",
                 "admissible_commands", "score", "max_score", "has_won",
                 "has_lost", "policy_commands", "intermediate_reward",
                 "action"]
        for prop in props:
            getattr(view, prop)


class TestGitGlulxMLEnvironment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.game = build_test_game()
        cls.tmpdir = tempfile.mkdtemp()
        cls.game_file = _compile_game(cls.game, folder=cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.env = textworld.start(self.game_file)
        self.env.activate_state_tracking()
        self.env.compute_intermediate_reward()
        self.game_state = self.env.reset()

    def tearDown(self):
        self.env.close()

    def test_activate_state_tracking(self):
        env = textworld.start(self.game_file)
        game_state = env.reset()
        npt.assert_raises(StateTrackingIsRequiredError, getattr,
                          game_state, 'admissible_commands')

    def test_compute_intermediate_reward(self):
        env = textworld.start(self.game_file)
        env.activate_state_tracking()
        game_state = env.reset()
        npt.assert_raises(OraclePolicyIsRequiredError, getattr,
                          game_state, 'intermediate_reward')

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
        env = textworld.start(self.game_file)
        npt.assert_raises(GameNotRunningError, env.step, "look")

        # Test sending command when the game is done.
        env = textworld.start(self.game_file)
        env.reset()
        env.step("quit")
        env.step("yes")
        npt.assert_raises(GameNotRunningError, env.step, "look")

        # Test sending empty command.
        env = textworld.start(self.game_file)
        env.reset()
        env.step("")

    def test_quit_no(self):
        env = textworld.start(self.game_file)
        env.reset()
        env.step("quit")
        env.step("no")
        env.step("look")


def test_missing_game_infos_file():
    with make_temp_directory() as tmpdir:
        game_file = pjoin(tmpdir, "tmp.ulx")
        with open(game_file, "w"):
            pass  # Empty file

        npt.assert_raises(MissingGameInfosError, textworld.start, game_file)
