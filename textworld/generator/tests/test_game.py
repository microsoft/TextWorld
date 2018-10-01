# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest

import numpy as np
import numpy.testing as npt

import textworld
from textworld import g_rng
from textworld import GameMaker
from textworld.utils import make_temp_directory

from textworld.generator import data
from textworld.generator import World
from textworld.generator import compile_game, make_game
from textworld.generator import make_small_map, make_grammar, make_game_with

from textworld.generator.chaining import ChainingOptions, sample_quest
from textworld.logic import Action, State

from textworld.generator.game import Quest, Game
from textworld.generator.game import QuestProgression, GameProgression
from textworld.generator.game import UnderspecifiedQuestError
from textworld.generator.game import ActionDependencyTree, ActionDependencyTreeElement
from textworld.generator.inform7 import gen_commands_from_actions

from textworld.logic import Proposition


def _apply_command(command: str, game_progression: GameProgression) -> None:
    """ Apply a text command to a game_progression object.
    """
    valid_commands = gen_commands_from_actions(game_progression.valid_actions, game_progression.game.infos)

    for action, cmd in zip(game_progression.valid_actions, valid_commands):
        if command == cmd:
            game_progression.update(action)
            return

    raise ValueError("Not a valid command: {}. Expected: {}".format(command, valid_commands))


def test_game_comparison():
    rngs = {}
    rngs['rng_map'] = np.random.RandomState(1)
    rngs['rng_objects'] = np.random.RandomState(2)
    rngs['rng_quest'] = np.random.RandomState(3)
    rngs['rng_grammar'] = np.random.RandomState(4)
    game1 = make_game(world_size=5, nb_objects=5, quest_length=2, quest_breadth=2, grammar_flags={}, rngs=rngs)

    rngs['rng_map'] = np.random.RandomState(1)
    rngs['rng_objects'] = np.random.RandomState(2)
    rngs['rng_quest'] = np.random.RandomState(3)
    rngs['rng_grammar'] = np.random.RandomState(4)
    game2 = make_game(world_size=5, nb_objects=5, quest_length=2, quest_breadth=2, grammar_flags={}, rngs=rngs)

    assert game1 == game2  # Test __eq__
    assert game1 in {game2}  # Test __hash__

    game3 = make_game(world_size=5, nb_objects=5, quest_length=2, quest_breadth=2, grammar_flags={}, rngs=rngs)
    assert game1 != game3


def test_variable_infos(verbose=False):
    g_rng.set_seed(1234)
    grammar_flags = {"theme": "house", "include_adj": True}
    game = textworld.generator.make_game(world_size=5, nb_objects=10, quest_length=3, quest_breadth=2, grammar_flags=grammar_flags)

    for var_id, var_infos in game.infos.items():
        if var_id not in ["P", "I"]:
            if verbose:
                print(var_infos.serialize())

            assert var_infos.id is not None
            assert var_infos.type is not None
            assert var_infos.name is not None
            assert var_infos.noun is not None
            assert var_infos.adj is not None
            assert var_infos.desc is not None


class TestQuest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        # The goal
        commands = ["go east", "insert carrot into chest"]

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
        chest = M.new(type='chest', name='chest')
        chest.add_property("open")
        R2.add(chest)

        cls.failing_conditions = (Proposition("eaten", [carrot.var]),)
        cls.quest = M.set_quest_from_commands(commands)
        cls.quest.set_failing_conditions(cls.failing_conditions)
        cls.game = M.build()

    def test_quest_creation(self):
        quest = Quest(self.quest.actions)
        assert quest.actions == self.quest.actions
        assert quest.win_action == self.quest.win_action
        assert quest.win_action.preconditions == self.quest.actions[-1].postconditions
        assert quest.fail_action is None

        quest = Quest(winning_conditions=self.quest.actions[-1].postconditions)
        assert len(quest.actions) == 0
        assert quest.win_action == self.quest.win_action
        assert quest.fail_action is None

        npt.assert_raises(UnderspecifiedQuestError, Quest, actions=[], winning_conditions=None)

        quest = Quest(self.quest.actions, failing_conditions=self.failing_conditions)
        assert quest.fail_action == self.quest.fail_action
        assert quest.fail_action.preconditions == self.failing_conditions

    def test_quest_serialization(self):
        data = self.quest.serialize()
        quest = Quest.deserialize(data)
        assert quest == self.quest

    def test_win_action(self):
        g_rng.set_seed(2018)
        map_ = make_small_map(n_rooms=5, possible_door_states=["open"])
        world = World.from_map(map_)

        for max_depth in range(1, 3):
            for rule in data.get_rules().values():
                options = ChainingOptions()
                options.backward = True
                options.max_depth = max_depth
                options.create_variables = True
                options.rules_per_depth = [[rule]]
                options.restricted_types = {"r"}
                chain = sample_quest(world.state, options)

                # Build the quest by providing the actions.
                actions = chain.actions
                assert len(actions) == max_depth, rule.name
                quest = Quest(actions)
                tmp_world = World.from_facts(chain.initial_state.facts)

                state = tmp_world.state
                for action in actions:
                    assert not state.is_applicable(quest.win_action)
                    state.apply(action)

                assert state.is_applicable(quest.win_action)

                # Build the quest by only providing the winning conditions.
                quest = Quest(actions=None, winning_conditions=actions[-1].postconditions)
                tmp_world = World.from_facts(chain.initial_state.facts)

                state = tmp_world.state
                for action in actions:
                    assert not state.is_applicable(quest.win_action)
                    state.apply(action)

                assert state.is_applicable(quest.win_action)

    def test_fail_action(self):
        state = self.game.world.state.copy()
        assert not state.is_applicable(self.quest.fail_action)

        from textworld.logic import Placeholder, Variable
        rules = self.game._game_logic.rules.values()
        constants_mapping = {Placeholder(t.name): Variable(t.name) for t in self.game._game_logic.types if t.constant}
        actions = list(state.all_applicable_actions(rules, constants_mapping))

        for action in actions:
            state = self.game.world.state.copy()
            state.apply(action)
            if action.name.startswith("eat"):
                assert state.is_applicable(self.quest.fail_action)
            else:
                assert not state.is_applicable(self.quest.fail_action)


class TestGame(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        # The goal
        commands = ["go east", "insert carrot into chest"]

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
        chest = M.new(type='chest', name='chest')
        chest.add_property("open")
        R2.add(chest)

        M.set_quest_from_commands(commands)
        cls.game = M.build()

    def test_directions_names(self):
        expected = set(["north", "south", "east", "west"])
        assert set(self.game.directions_names) == expected

    def test_objects_types(self):
        expected_types = set(t.name for t in data.get_types())
        assert set(self.game.objects_types) == expected_types

    def test_objects_names(self):
        expected_names = {"chest", "carrot", "wooden door"}
        assert set(self.game.objects_names) == expected_names

    def test_objects_names_and_types(self):
        expected_names_types = {("chest", "chest"), ("carrot", "f"), ("wooden door", "d")}
        assert set(self.game.objects_names_and_types) == expected_names_types

    def test_verbs(self):
        expected_verbs = {"drop", "take", "insert", "put", "open", "close",
                          "lock", "unlock", "go", "eat", "look",
                          "inventory", "examine", "wait"}
        assert set(self.game.verbs) == expected_verbs

    def test_serialization(self):
        data = self.game.serialize()
        game2 = Game.deserialize(data)
        assert self.game == game2
        assert self.game.metadata == game2.metadata


class TestQuestProgression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        # Create a 'bedroom' room.
        R1 = M.new_room("bedroom")
        R2 = M.new_room("kitchen")
        M.set_player(R2)

        path = M.connect(R1.east, R2.west)
        path.door = M.new(type='d', name='wooden door')
        path.door.add_property("closed")

        carrot = M.new(type='f', name='carrot')
        R1.add(carrot)

        # Add a closed chest in R2.
        chest = M.new(type='chest', name='chest')
        chest.add_property("open")
        R2.add(chest)

        # The goal
        commands = ["open wooden door", "go west", "take carrot", "go east", "drop carrot"]
        cls.quest = M.set_quest_from_commands(commands)

        commands = ["open wooden door", "go west", "take carrot", "eat carrot"]
        cls.eating_quest = M.new_quest_using_commands(commands)

        cls.game = M.build()

    def test_winning_policy(self):
        quest = QuestProgression(self.quest)
        assert quest.winning_policy == self.quest.actions
        quest.update(self.quest.actions[0], state=State())
        assert tuple(quest.winning_policy) == self.quest.actions[1:]

    def test_failing_quest(self):
        quest = QuestProgression(self.quest)

        state = self.game.state.copy()
        for action in self.eating_quest.actions:
            state.apply(action)
            if action.name.startswith("eat"):
                quest.update(action, state)
                assert len(quest.winning_policy) == 0
                assert quest.done
                assert not quest.completed
                assert not quest.failed
                assert quest.unfinishable
                break

            assert not quest.done
            assert len(quest.winning_policy) > 0


class TestGameProgression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        # The goal
        commands = ["open wooden door", "go west", "take carrot", "go east", "drop carrot"]

        # Create a 'bedroom' room.
        R1 = M.new_room("bedroom")
        R2 = M.new_room("kitchen")
        M.set_player(R2)

        path = M.connect(R1.east, R2.west)
        path.door = M.new(type='d', name='wooden door')
        path.door.add_property("closed")

        carrot = M.new(type='f', name='carrot')
        R1.add(carrot)

        # Add a closed chest in R2.
        chest = M.new(type='chest', name='chest')
        chest.add_property("open")
        R2.add(chest)

        cls.quest = M.set_quest_from_commands(commands)
        cls.game = M.build()

    def test_is_game_completed(self):
        game_progress = GameProgression(self.game)

        for action in self.quest.actions:
            assert not game_progress.done
            game_progress.update(action)

        assert game_progress.done

    def test_cycle_in_winning_policy(self):
        M = GameMaker()

        # Create a map.
        # r0
        #  |
        # r1 -- r2
        #  |    |
        # r3 -- r4
        R0 = M.new_room("r0")
        R1 = M.new_room("r1")
        R2 = M.new_room("r2")
        R3 = M.new_room("r3")
        R4 = M.new_room("r4")
        M.set_player(R1)

        M.connect(R0.south, R1.north),
        M.connect(R1.east, R2.west),
        M.connect(R3.east, R4.west)
        M.connect(R1.south, R3.north)
        M.connect(R2.south, R4.north)

        carrot = M.new(type='f', name='carrot')
        R0.add(carrot)

        apple = M.new(type='f', name='apple')
        R2.add(apple)

        commands = ["go north", "take carrot"]
        M.set_quest_from_commands(commands)
        game = M.build()
        game_progression = GameProgression(game)

        _apply_command("go south", game_progression)
        expected_commands = ["go north"] + commands
        winning_commands = gen_commands_from_actions(game_progression.winning_policy, game.infos)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go east", game_progression)
        _apply_command("go north", game_progression)
        expected_commands = ["go south", "go west", "go north"] + commands
        winning_commands = gen_commands_from_actions(game_progression.winning_policy, game.infos)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go west", game_progression)  # Found shortcut
        expected_commands = commands
        winning_commands = gen_commands_from_actions(game_progression.winning_policy, game.infos)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        # Quest where player's has to pick up the carrot first.
        commands = ["go east", "take apple", "go west", "go north", "drop apple"]

        M.set_quest_from_commands(commands)
        game = M.build()
        game_progression = GameProgression(game)

        _apply_command("go south", game_progression)
        expected_commands = ["go north"] + commands
        winning_commands = gen_commands_from_actions(game_progression.winning_policy, game.infos)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go east", game_progression)
        expected_commands = ["go west", "go north"] + commands
        winning_commands = gen_commands_from_actions(game_progression.winning_policy, game.infos)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go north", game_progression)  # Found shortcut
        expected_commands = commands[1:]
        winning_commands = gen_commands_from_actions(game_progression.winning_policy, game.infos)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

    def test_game_with_multiple_quests(self):
        M = GameMaker()

        # The subgoals (needs to be executed in order).
        commands = [["open wooden door", "go west", "take carrot", "go east", "drop carrot"],
                    # Now, the player is back in the kitchen and the wooden door is open.
                    ["go west", "take lettuce", "go east", "drop lettuce"],
                    # Now, the player is back in the kitchen, there are a carrot and a lettuce on the floor.
                    ["take lettuce", "take carrot", "insert carrot into chest", "insert lettuce into chest", "close chest"]]

        # Create a 'bedroom' room.
        R1 = M.new_room("bedroom")
        R2 = M.new_room("kitchen")
        M.set_player(R2)

        path = M.connect(R1.east, R2.west)
        path.door = M.new(type='d', name='wooden door')
        path.door.add_property("closed")

        carrot = M.new(type='f', name='carrot')
        lettuce = M.new(type='f', name='lettuce')
        M.add_fact("edible", carrot)
        M.add_fact("edible", lettuce)
        R1.add(carrot, lettuce)

        # Add a closed chest in R2.
        chest = M.new(type='chest', name='chest')
        chest.add_property("open")
        R2.add(chest)

        quest1 = M.new_quest_using_commands(commands[0])
        quest1.desc = "Fetch the carrot and drop it on the kitchen's ground."
        quest2 = M.new_quest_using_commands(commands[0] + commands[1])
        quest2.desc = "Fetch the lettuce and drop it on the kitchen's ground."
        quest3 = M.new_quest_using_commands(commands[0] + commands[1] + commands[2])
        winning_facts = [M.new_fact("in", lettuce, chest),
                         M.new_fact("in", carrot, chest),
                         M.new_fact("closed", chest),]
        quest3.set_winning_conditions(winning_facts)
        quest3.desc = "Put the lettuce and the carrot into the chest before closing it."

        M._quests = [quest1, quest2, quest3]
        assert len(M._quests) == len(commands)
        game = M.build()

        game_progress = GameProgression(game)
        assert len(game_progress.quest_progressions) == len(game.quests)

        # Following the actions associated to the last quest actually corresponds
        # to solving the whole game.
        for action in game_progress.winning_policy:
            assert not game_progress.done
            game_progress.update(action)

        assert game_progress.done
        assert all(quest_progression.done for quest_progression in game_progress.quest_progressions)

        # Try solving the game by greedily taking the first action from the current winning policy.
        game_progress = GameProgression(game)
        while not game_progress.done:
            action = game_progress.winning_policy[0]
            game_progress.update(action)
            # print(action.name, [c.name for c in game_progress.winning_policy])

        # Try solving the second quest (i.e. bringing back the lettuce) first.
        game_progress = GameProgression(game)
        for command in ["open wooden door", "go west", "take lettuce", "go east", "drop lettuce"]:
            _apply_command(command, game_progress)

        assert not game_progress.quest_progressions[0].done
        assert game_progress.quest_progressions[1].done

        for command in ["go west", "take carrot", "go east", "drop carrot"]:
            _apply_command(command, game_progress)

        assert game_progress.quest_progressions[0].done
        assert game_progress.quest_progressions[1].done

        for command in ["take lettuce", "take carrot", "insert carrot into chest", "insert lettuce into chest", "close chest"]:
            _apply_command(command, game_progress)

        assert game_progress.done

        # Game is done whenever a quest has failed or is unfinishable.
        game_progress = GameProgression(game)

        for command in ["open wooden door", "go west", "take carrot", "eat carrot"]:
            assert not game_progress.done
            _apply_command(command, game_progress)

        assert game_progress.done

    def test_game_without_a_quest(self):
        M = GameMaker()

        room = M.new_room()
        M.set_player(room)
        item = M.new(type="o")
        room.add(item)

        game = M.build()
        game_progress = GameProgression(game)
        assert not game_progress.done

        # Simulate action that doesn't change the world.
        action = game_progress.valid_actions[0]
        game_progress.update(action)
        assert not game_progress.done


class TestActionDependencyTree(unittest.TestCase):

    def test_flatten(self):
        action_lock = Action.parse("lock/c :: $at(P, r) & $at(c, r) & $match(k, c) & $in(k, I) & closed(c) -> locked(c)")
        action_close = Action.parse("close/c :: $at(P, r) & $at(c, r) & open(c) -> closed(c)")
        action_insert1 = Action.parse("insert :: $at(P, r) & $at(c, r) & $open(c) & in(o1: o, I) -> in(o1: o, c)")
        action_insert2 = Action.parse("insert :: $at(P, r) & $at(c, r) & $open(c) & in(o2: o, I) -> in(o2: o, c)")
        action_take1 = Action.parse("take :: $at(P, r) & at(o1: o, r) -> in(o1: o, I)")
        action_take2 = Action.parse("take :: $at(P, r) & at(o2: o, r) -> in(o2: o, I)")
        action_win = Action.parse("win :: $in(o1: o, c) & $in(o2: o, c) & $locked(c) -> win(o1: o, o2: o, c)")

        tree = ActionDependencyTree(element_type=ActionDependencyTreeElement)
        tree.push(action_win)
        tree.push(action_lock)
        tree.push(action_close)
        tree.push(action_insert1)
        tree.push(action_insert2)
        tree.push(action_take1)
        tree.push(action_take2)
        actions = list(a.name for a in tree.flatten())
        assert actions == ['take', 'insert', 'take', 'insert', 'close/c', 'lock/c', 'win'], actions
