# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest
import textwrap
from typing import Iterable

import numpy as np
import numpy.testing as npt

import textworld
from textworld import g_rng
from textworld import GameMaker
from textworld.utils import make_temp_directory

from textworld.generator.data import KnowledgeBase
from textworld.generator import World
from textworld.generator import make_small_map, make_grammar, make_game_with

from textworld.generator.chaining import ChainingOptions, sample_quest
from textworld.logic import Action, State

from textworld.generator.game import Quest, Game, Event
from textworld.generator.game import QuestProgression, GameProgression, EventProgression
from textworld.generator.game import UnderspecifiedEventError, UnderspecifiedQuestError
from textworld.generator.game import ActionDependencyTree, ActionDependencyTreeElement
from textworld.generator.inform7 import Inform7Game

from textworld.logic import Proposition


def _find_action(command: str, actions: Iterable[Action], inform7: Inform7Game) -> None:
    """ Apply a text command to a game_progression object. """
    commands = inform7.gen_commands_from_actions(actions)
    for action, cmd in zip(actions, commands):
        if command == cmd:
            return action

    raise ValueError("No action found matching command: {}.".format(command))


def _apply_command(command: str, game_progression: GameProgression, inform7: Inform7Game) -> None:
    """ Apply a text command to a game_progression object. """
    action = _find_action(command, game_progression.valid_actions, inform7)
    game_progression.update(action)


def test_game_comparison():
    options = textworld.GameOptions()
    options.nb_rooms = 5
    options.nb_objects = 5
    options.quest_length = 2
    options.quest_breadth = 2
    options.seeds = {"map": 1, "objects": 2, "quest": 3, "grammar": 4}
    game1 = textworld.generator.make_game(options)
    game2 = textworld.generator.make_game(options)

    assert game1 == game2  # Test __eq__
    assert game1 in {game2}  # Test __hash__

    options = options.copy()
    options.seeds = {"map": 4, "objects": 3, "quest": 2, "grammar": 1}
    game3 = textworld.generator.make_game(options)
    assert game1 != game3


def test_variable_infos(verbose=False):
    options = textworld.GameOptions()
    options.nb_rooms = 5
    options.nb_objects = 10
    options.quest_length = 3
    options.quest_breadth = 2
    options.seeds = 1234
    options.grammar.theme = "house"
    options.grammar.include_adj = True

    game = textworld.generator.make_game(options)

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


class TestEvent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        # The goal
        commands = ["take carrot", "insert carrot into chest"]

        R1 = M.new_room("room")
        M.set_player(R1)

        carrot = M.new(type='f', name='carrot')
        R1.add(carrot)

        # Add a closed chest in R2.
        chest = M.new(type='c', name='chest')
        chest.add_property("open")
        R1.add(chest)

        cls.event = M.new_event_using_commands(commands)
        cls.actions = cls.event.actions
        cls.conditions = {M.new_fact("in", carrot, chest)}

    def test_init(self):
        event = Event(self.actions)
        assert event.actions == self.actions
        assert event.condition == self.event.condition
        assert event.condition.preconditions == self.actions[-1].postconditions
        assert set(event.condition.preconditions).issuperset(self.conditions)

        event = Event(conditions=self.conditions)
        assert len(event.actions) == 0
        assert set(event.condition.preconditions) == set(self.conditions)

        npt.assert_raises(UnderspecifiedEventError, Event, actions=[])
        npt.assert_raises(UnderspecifiedEventError, Event, actions=[], conditions=[])
        npt.assert_raises(UnderspecifiedEventError, Event, conditions=[])

    def test_serialization(self):
        data = self.event.serialize()
        event = Event.deserialize(data)
        assert event == self.event

    def test_copy(self):
        event = self.event.copy()
        assert event == self.event
        assert id(event) != id(self.event)


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
        chest = M.new(type='c', name='chest')
        chest.add_property("open")
        R2.add(chest)

        cls.eventA = M.new_event_using_commands(commands)
        cls.eventB = Event(conditions={M.new_fact("at", carrot, R1),
                                            M.new_fact("closed", path.door)})
        cls.eventC = Event(conditions={M.new_fact("eaten", carrot)})
        cls.eventD = Event(conditions={M.new_fact("closed", chest),
                                            M.new_fact("closed", path.door)})
        cls.quest = Quest(win_events=[cls.eventA, cls.eventB],
                          fail_events=[cls.eventC, cls.eventD],
                          reward=2)

        M.quests = [cls.quest]
        cls.game = M.build()
        cls.inform7 = Inform7Game(cls.game)

    def test_init(self):
        npt.assert_raises(UnderspecifiedQuestError, Quest)

        quest = Quest(win_events=[self.eventA, self.eventB])
        assert len(quest.fail_events) == 0

        quest = Quest(fail_events=[self.eventC, self.eventD])
        assert len(quest.win_events) == 0

        quest = Quest(win_events=[self.eventA],
                      fail_events=[self.eventC, self.eventD])

        assert len(quest.win_events) > 0
        assert len(quest.fail_events) > 0

    def test_serialization(self):
        data = self.quest.serialize()
        quest = Quest.deserialize(data)
        assert quest == self.quest
        assert id(quest) != id(self.quest)

    def test_copy(self):
        quest = self.quest.copy()
        assert quest == self.quest
        assert id(quest) != id(self.quest)

    def test_generating_quests(self):
        g_rng.set_seed(2018)
        map_ = make_small_map(n_rooms=5, possible_door_states=["open"])
        world = World.from_map(map_)

        for max_depth in range(1, 3):
            for rule in KnowledgeBase.default().rules.values():
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
                quest = Quest(win_events=[Event(actions)])
                tmp_world = World.from_facts(chain.initial_state.facts)

                state = tmp_world.state
                for action in actions:
                    assert not quest.is_winning(state)
                    state.apply(action)

                assert quest.is_winning(state)

                # Build the quest by only providing the winning conditions.
                quest = Quest(win_events=[Event(conditions=actions[-1].postconditions)])
                tmp_world = World.from_facts(chain.initial_state.facts)

                state = tmp_world.state
                for action in actions:
                    assert not quest.is_winning(state)
                    state.apply(action)

                assert quest.is_winning(state)

    def test_win_actions(self):
        state = self.game.world.state.copy()
        for action in self.quest.win_events[0].actions:
            assert not self.quest.is_winning(state)
            state.apply(action)

        assert self.quest.is_winning(state)

        # Test alternative way of winning,
        # i.e. dropping the carrot and closing the door.
        state = self.game.world.state.copy()
        actions = list(state.all_applicable_actions(self.game.kb.rules.values(),
                                                    self.game.kb.types.constants_mapping))

        drop_carrot = _find_action("drop carrot", actions, self.inform7)
        close_door = _find_action("close wooden door", actions, self.inform7)

        state = self.game.world.state.copy()
        assert state.apply(drop_carrot)
        assert not self.quest.is_winning(state)
        assert state.apply(close_door)
        assert self.quest.is_winning(state)

        # Or the other way around.
        state = self.game.world.state.copy()
        assert state.apply(close_door)
        assert not self.quest.is_winning(state)
        assert state.apply(drop_carrot)
        assert self.quest.is_winning(state)

    def test_fail_actions(self):
        state = self.game.world.state.copy()
        assert not self.quest.is_failing(state)

        actions = list(state.all_applicable_actions(self.game.kb.rules.values(),
                                                    self.game.kb.types.constants_mapping))
        eat_carrot = _find_action("eat carrot", actions, self.inform7)
        go_east = _find_action("go east", actions, self.inform7)

        for action in actions:
            state = self.game.world.state.copy()
            state.apply(action)
            # Only the `eat carrot` should fail.
            assert self.quest.is_failing(state) == (action == eat_carrot)

        state = self.game.world.state.copy()
        state.apply(go_east)  # Move to the kitchen.
        actions = list(state.all_applicable_actions(self.game.kb.rules.values(),
                                                    self.game.kb.types.constants_mapping))
        close_door = _find_action("close wooden door", actions, self.inform7)
        close_chest = _find_action("close chest", actions, self.inform7)

        # Only closing the door doesn't fail the quest.
        state_ = state.apply_on_copy(close_door)
        assert not self.quest.is_failing(state_)

        # Only closing the chest doesn't fail the quest.
        state_ = state.apply_on_copy(close_chest)
        assert not self.quest.is_failing(state_)

        # Closing the chest, then the door should fail the quest.
        state_ = state.apply_on_copy(close_chest)
        state_.apply(close_door)
        assert self.quest.is_failing(state_)

        # Closing the door, then the chest should fail the quest.
        state_ = state.apply_on_copy(close_door)
        state_.apply(close_chest)
        assert self.quest.is_failing(state_)


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
        chest = M.new(type='c', name='chest')
        chest.add_property("open")
        R2.add(chest)

        M.set_quest_from_commands(commands)
        cls.game = M.build()

    def test_directions_names(self):
        expected = set(["north", "south", "east", "west"])
        assert set(self.game.directions_names) == expected

    def test_objects_types(self):
        expected_types = set(KnowledgeBase.default().types.types)
        assert set(self.game.objects_types) == expected_types

    def test_objects_names(self):
        expected_names = {"chest", "carrot", "wooden door"}
        assert set(self.game.objects_names) == expected_names

    def test_objects_names_and_types(self):
        expected_names_types = {("chest", "c"), ("carrot", "f"), ("wooden door", "d")}
        assert set(self.game.objects_names_and_types) == expected_names_types

    def test_verbs(self):
        expected_verbs = {"drop", "take", "insert", "put", "open", "close",
                          "lock", "unlock", "go", "eat", "look",
                          "inventory", "examine", "wait"}
        assert set(self.game.verbs) == expected_verbs

    def test_serialization(self):
        data = self.game.serialize()
        game = Game.deserialize(data)
        assert game == self.game
        assert id(game) != id(self.game)
        assert game.metadata == self.game.metadata

    def test_copy(self):
        game = self.game.copy()
        assert game == self.game
        assert id(game) != id(self.game)
        assert game.metadata == self.game.metadata


class TestEventProgression(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        # The goal
        commands = ["take carrot", "insert carrot into chest"]

        R1 = M.new_room("room")
        M.set_player(R1)

        carrot = M.new(type='f', name='carrot')
        R1.add(carrot)

        # Add a closed chest in R2.
        chest = M.new(type='c', name='chest')
        chest.add_property("open")
        R1.add(chest)

        cls.event = M.new_event_using_commands(commands)
        cls.actions = cls.event.actions
        cls.conditions = {M.new_fact("in", carrot, chest)}
        cls.game = M.build()
        commands = ["take carrot", "eat carrot"]
        cls.eating_carrot = M.new_event_using_commands(commands)

    def test_triggering_policy(self):
        event = EventProgression(self.event, KnowledgeBase.default())

        state = self.game.world.state.copy()
        expected_actions = self.event.actions
        for i, action in enumerate(expected_actions):
            assert event.triggering_policy == expected_actions[i:]
            assert not event.done
            assert not event.triggered
            assert not event.untriggerable
            state.apply(action)
            event.update(action=action, state=state)

        assert event.triggering_policy == ()
        assert event.done
        assert event.triggered
        assert not event.untriggerable

    def test_untriggerable(self):
        event = EventProgression(self.event, KnowledgeBase.default())

        state = self.game.world.state.copy()
        for action in self.eating_carrot.actions:
            assert event.triggering_policy != ()
            assert not event.done
            assert not event.triggered
            assert not event.untriggerable
            state.apply(action)
            event.update(action=action, state=state)

        assert event.triggering_policy == ()
        assert event.done
        assert not event.triggered
        assert event.untriggerable


class TestQuestProgression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        M = GameMaker()

        room = M.new_room("room")
        M.set_player(room)

        carrot = M.new(type='f', name='carrot')
        lettuce = M.new(type='f', name='lettuce')
        room.add(carrot)
        room.add(lettuce)

        chest = M.new(type='c', name='chest')
        chest.add_property("open")
        room.add(chest)

        # The goals
        commands = ["take carrot", "insert carrot into chest"]
        cls.eventA = M.new_event_using_commands(commands)

        commands = ["take lettuce", "insert lettuce into chest", "close chest"]
        event = M.new_event_using_commands(commands)
        cls.eventB = Event(actions=event.actions,
                                conditions={M.new_fact("in", lettuce, chest),
                                            M.new_fact("closed", chest)})

        cls.fail_eventA = Event(conditions={M.new_fact("eaten", carrot)})
        cls.fail_eventB = Event(conditions={M.new_fact("eaten", lettuce)})

        cls.quest = Quest(win_events=[cls.eventA, cls.eventB],
                          fail_events=[cls.fail_eventA, cls.fail_eventB])

        commands = ["take carrot", "eat carrot"]
        cls.eating_carrot = M.new_event_using_commands(commands)
        commands = ["take lettuce", "eat lettuce"]
        cls.eating_lettuce = M.new_event_using_commands(commands)
        commands = ["take lettuce", "insert lettuce into chest"]

        M.quests = [cls.quest]
        cls.game = M.build()

    def _apply_actions_to_quest(self, actions, quest):
        state = self.game.world.state.copy()
        for action in actions:
            assert not quest.done
            state.apply(action)
            quest.update(action, state)

        assert quest.done
        return quest

    def test_completed(self):
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventA.actions, quest)
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None

        # Alternative winning strategy.
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventB.actions, quest)
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None

    def test_failed(self):
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eating_carrot.actions, quest)
        assert not quest.completed
        assert quest.failed
        assert quest.winning_policy is None

        quest = QuestProgression(self.quest, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eating_lettuce.actions, quest)
        assert not quest.completed
        assert quest.failed
        assert quest.winning_policy is None

    def test_winning_policy(self):
        kb = KnowledgeBase.default()
        quest = QuestProgression(self.quest, kb)
        quest = self._apply_actions_to_quest(quest.winning_policy, quest)
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None

        # Winning policy should be the shortest one leading to a winning event.
        state = self.game.world.state.copy()
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        for i, action in enumerate(self.eventB.actions):
            if i < 2:
                assert quest.winning_policy == self.eventA.actions
            else:
                # After taking the lettuce and putting it in the chest,
                # QuestB becomes the shortest one to complete.
                assert quest.winning_policy == self.eventB.actions[i:]
            assert not quest.done
            state.apply(action)
            quest.update(action, state)

        assert quest.done
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None


class TestGameProgression(unittest.TestCase):

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
        lettuce = M.new(type='f', name='lettuce')
        R1.add(carrot)
        R1.add(lettuce)

        # Add a closed chest in R2.
        chest = M.new(type='c', name='chest')
        chest.add_property("open")
        R2.add(chest)

        # The goals
        commands = ["open wooden door", "go west", "take carrot", "go east", "drop carrot"]
        cls.eventA = M.new_event_using_commands(commands)

        commands = ["open wooden door", "go west", "take lettuce", "go east", "insert lettuce into chest"]
        cls.eventB = M.new_event_using_commands(commands)

        cls.losing_eventA = Event(conditions={M.new_fact("eaten", carrot)})
        cls.losing_eventB = Event(conditions={M.new_fact("eaten", lettuce)})

        cls.questA = Quest(win_events=[cls.eventA], fail_events=[cls.losing_eventA])
        cls.questB = Quest(win_events=[cls.eventB], fail_events=[cls.losing_eventB])
        cls.questC = Quest(win_events=[], fail_events=[cls.losing_eventA, cls.losing_eventB])

        commands = ["open wooden door", "go west", "take lettuce", "go east", "insert lettuce into chest"]
        cls.questC = M.new_quest_using_commands(commands)

        commands = ["open wooden door", "go west", "take carrot", "eat carrot"]
        cls.eating_carrot = M.new_event_using_commands(commands)
        commands = ["open wooden door", "go west", "take lettuce", "eat lettuce"]
        cls.eating_lettuce = M.new_event_using_commands(commands)
        commands = ["open wooden door", "go west", "take lettuce", "go east", "insert lettuce into chest"]

        M.quests = [cls.questA, cls.questB]
        cls.game = M.build()

    def test_completed(self):
        game = GameProgression(self.game)
        for action in self.eventA.actions:
            assert not game.done
            game.update(action)

        assert not game.done
        remaining_actions = self.eventB.actions[1:]  # skipping "open door".
        assert game.winning_policy == remaining_actions

        for action in self.eventB.actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert game.completed
        assert not game.failed
        assert game.winning_policy is None

    def test_failed(self):
        game = GameProgression(self.game)
        for action in self.eating_carrot.actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert not game.completed
        assert game.failed
        assert game.winning_policy is None

        game = GameProgression(self.game)
        for action in self.eating_lettuce.actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert not game.completed
        assert game.failed
        assert game.winning_policy is None

        # Completing QuestA but failing quest B.
        game = GameProgression(self.game)
        for action in self.eventA.actions:
            assert not game.done
            game.update(action)

        assert not game.done

        game = GameProgression(self.game)
        for action in self.eating_lettuce.actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert not game.completed
        assert game.failed
        assert game.winning_policy is None

    def test_winning_policy(self):
        # Test following the winning policy derived from the quests.
        game_progress = GameProgression(self.game)
        for action in game_progress.winning_policy:
            assert not game_progress.done
            game_progress.update(action)

        assert game_progress.done
        assert game_progress.completed
        assert not game_progress.failed
        assert game_progress.winning_policy is None

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
        inform7 = Inform7Game(game)
        game_progression = GameProgression(game)

        _apply_command("go south", game_progression, inform7)
        expected_commands = ["go north"] + commands
        winning_commands = inform7.gen_commands_from_actions(game_progression.winning_policy)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go east", game_progression, inform7)
        _apply_command("go north", game_progression, inform7)
        expected_commands = ["go south", "go west", "go north"] + commands
        winning_commands = inform7.gen_commands_from_actions(game_progression.winning_policy)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go west", game_progression, inform7)  # Found shortcut
        expected_commands = commands
        winning_commands = inform7.gen_commands_from_actions(game_progression.winning_policy)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        # Quest where player's has to pick up the carrot first.
        commands = ["go east", "take apple", "go west", "go north", "drop apple"]

        M.set_quest_from_commands(commands)
        game = M.build()
        game_progression = GameProgression(game)

        _apply_command("go south", game_progression, inform7)
        expected_commands = ["go north"] + commands
        winning_commands = inform7.gen_commands_from_actions(game_progression.winning_policy)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go east", game_progression, inform7)
        expected_commands = ["go west", "go north"] + commands
        winning_commands = inform7.gen_commands_from_actions(game_progression.winning_policy)
        assert winning_commands == expected_commands, "{} != {}".format(winning_commands, expected_commands)

        _apply_command("go north", game_progression, inform7)  # Found shortcut
        expected_commands = commands[1:]
        winning_commands = inform7.gen_commands_from_actions(game_progression.winning_policy)
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
        R1.add(carrot, lettuce)

        # Add a closed chest in R2.
        chest = M.new(type='c', name='chest')
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
        quest3.win_events[0].set_conditions(winning_facts)
        quest3.desc = "Put the lettuce and the carrot into the chest before closing it."

        M.quests = [quest1, quest2, quest3]
        assert len(M.quests) == len(commands)
        game = M.build()

        inform7 = Inform7Game(game)
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
            _apply_command(command, game_progress, inform7)

        assert not game_progress.quest_progressions[0].done
        assert game_progress.quest_progressions[1].done

        for command in ["go west", "take carrot", "go east", "drop carrot"]:
            _apply_command(command, game_progress, inform7)

        assert game_progress.quest_progressions[0].done
        assert game_progress.quest_progressions[1].done

        for command in ["take lettuce", "take carrot", "insert carrot into chest", "insert lettuce into chest", "close chest"]:
            _apply_command(command, game_progress, inform7)

        assert game_progress.done

        # Game is done whenever a quest has failed or is unfinishable.
        game_progress = GameProgression(game)

        for command in ["open wooden door", "go west", "take carrot", "eat carrot"]:
            assert not game_progress.done
            _apply_command(command, game_progress, inform7)

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
        assert game_progress.winning_policy is None

        # Simulate action that doesn't change the world.
        action = game_progress.valid_actions[0]
        game_progress.update(action)
        assert not game_progress.done


class TestActionDependencyTree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
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
        cls.tree = tree

    def test_flatten(self):
        actions = list(a.name for a in self.tree.flatten())
        assert actions == ['take', 'insert', 'take', 'insert', 'close/c', 'lock/c', 'win'], actions

    def test_str(self):
        expected = textwrap.dedent("""\
        win(o1: o, c, o2: o)
          lock/c(P, r, c, k, I)
            close/c(P, r, c)
          insert(P, r, c, o1: o, I)
            take(P, r, o1: o, I)
          insert(P, r, c, o2: o, I)
            take(P, r, o2: o, I)""")
        assert expected == str(self.tree)
