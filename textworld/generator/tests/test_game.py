# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest
import textwrap
from typing import Iterable

import textworld
from textworld import g_rng
from textworld import GameMaker

from textworld.generator.data import KnowledgeBase
from textworld.generator import World
from textworld.generator import make_small_map

from textworld.generator.chaining import ChainingOptions, sample_quest
from textworld.logic import Action, State, Proposition, Rule
from textworld.generator.game import GameOptions
from textworld.generator.game import Quest, Game, Event, EventAction, EventCondition, EventOr, EventAnd
from textworld.generator.game import QuestProgression, GameProgression, EventProgression
from textworld.generator.game import ActionDependencyTree, ActionDependencyTreeElement
from textworld.generator.inform7 import Inform7Game

from textworld.logic import GameLogic


def _build_game():
    M = GameMaker()

    # The goal
    quest1_cmds1 = ["open chest", "take carrot", "insert carrot into chest", "close chest"]
    quest1_cmds2 = ["open chest", "take onion", "insert onion into chest", "close chest"]
    quest2_cmds = ["take knife", "put knife on counter"]

    kitchen = M.new_room("kitchen")
    M.set_player(kitchen)

    counter = M.new(type='s', name='counter')
    chest = M.new(type='c', name='chest')
    chest.add_property("closed")
    carrot = M.new(type='f', name='carrot')
    onion = M.new(type='f', name='onion')
    knife = M.new(type='o', name='knife')
    kitchen.add(chest, counter, carrot, onion, knife)

    carrot_in_chest = EventCondition(conditions={M.new_fact("in", carrot, chest)})
    onion_in_chest = EventCondition(conditions={M.new_fact("in", onion, chest)})
    closing_chest = EventAction(action=M.new_action("close/c", chest))

    either_carrot_or_onion_in_chest = EventOr(events=(carrot_in_chest, onion_in_chest))
    closing_chest_with_either_carrot_or_onion = EventAnd(events=(either_carrot_or_onion_in_chest, closing_chest))

    carrot_in_inventory = EventCondition(conditions={M.new_fact("in", carrot, M.inventory)})
    closing_chest_without_carrot = EventAnd(events=(carrot_in_inventory, closing_chest))

    eating_carrot = EventAction(action=M.new_action("eat", carrot))
    onion_eaten = EventCondition(conditions={M.new_fact("eaten", onion)})

    quest1 = Quest(
        win_event=closing_chest_with_either_carrot_or_onion,
        fail_event=EventOr([
            closing_chest_without_carrot,
            EventAnd([
                eating_carrot,
                onion_eaten
            ])
        ])
    )

    knife_on_counter = EventCondition(conditions={M.new_fact("on", knife, counter)})

    quest2 = Quest(
        win_event=knife_on_counter,
    )

    carrot_in_chest.name = "carrot_in_chest"
    onion_in_chest.name = "onion_in_chest"
    closing_chest.name = "closing_chest"
    either_carrot_or_onion_in_chest.name = "either_carrot_or_onion_in_chest"
    closing_chest_with_either_carrot_or_onion.name = "closing_chest_with_either_carrot_or_onion"
    carrot_in_inventory.name = "carrot_in_inventory"
    closing_chest_without_carrot.name = "closing_chest_without_carrot"
    eating_carrot.name = "eating_carrot"
    onion_eaten.name = "onion_eaten"
    knife_on_counter.name = "knife_on_counter"

    M.quests = [quest1, quest2]
    M.set_walkthrough(
        quest1_cmds1,
        quest1_cmds2,
        quest2_cmds
    )
    game = M.build()

    eating_carrot.commands = ["take carrot", "eat carrot"]
    eating_carrot.actions = M.get_action_from_commands(eating_carrot.commands)
    onion_eaten.commands = ["take onion", "eat onion"]
    onion_eaten.actions = M.get_action_from_commands(onion_eaten.commands)
    closing_chest_without_carrot.commands = ["take carrot", "open chest", "close chest"]
    closing_chest_without_carrot.actions = M.get_action_from_commands(closing_chest_without_carrot.commands)
    knife_on_counter.commands = ["take knife", "put knife on counter"]
    knife_on_counter.actions = M.get_action_from_commands(knife_on_counter.commands)

    data = {
        "game": game,
        "quest": quest1,
        "quest1": quest1,
        "quest2": quest2,
        "carrot_in_chest": carrot_in_chest,
        "onion_in_chest": onion_in_chest,
        "closing_chest": closing_chest,
        "either_carrot_or_onion_in_chest": either_carrot_or_onion_in_chest,
        "closing_chest_with_either_carrot_or_onion": closing_chest_with_either_carrot_or_onion,
        "carrot_in_inventory": carrot_in_inventory,
        "closing_chest_without_carrot": closing_chest_without_carrot,
        "eating_carrot": eating_carrot,
        "onion_eaten": onion_eaten,
        "knife_on_counter": knife_on_counter,
    }

    return data


DATA = _build_game()


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
    options.chaining.max_depth = 2
    options.chaining.max_breadth = 2
    options.seeds = {"map": 1, "objects": 2, "quest": 3, "grammar": 4}
    game1 = textworld.generator.make_game(options)
    game2 = textworld.generator.make_game(options)

    assert game1 == game2  # Test __eq__
    assert game1 in {game2}  # Test __hash__

    options = options.copy()
    options.seeds = {"map": 4, "objects": 3, "quest": 2, "grammar": 1}
    game3 = textworld.generator.make_game(options)
    assert game1 != game3


def test_reloading_game_with_custom_kb():
    twl = KnowledgeBase.default().logic._document
    twl += """
        type customobj : o {
            inform7 {
                type {
                    kind :: "custom-obj-like";
                }
            }
        }
    """

    logic = GameLogic.parse(twl)
    options = GameOptions()
    options.kb = KnowledgeBase(logic, "")
    M = GameMaker(options)

    room = M.new_room("room")
    M.set_player(room)

    custom_obj = M.new(type='customobj', name='customized object')
    M.inventory.add(custom_obj)

    commands = ["drop customized object"]
    quest = M.set_quest_from_commands(commands)
    assert quest.commands == tuple(commands)
    game = M.build()
    assert game == Game.deserialize(game.serialize())


def test_variable_infos(verbose=False):
    options = textworld.GameOptions()
    options.nb_rooms = 5
    options.nb_objects = 10
    options.chaining.max_depth = 3
    options.chaining.max_breadth = 2
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

    def test_init(self):
        event = Event(conditions=[Proposition.parse("in(carrot: f, chest: c)")])
        assert type(event) is EventCondition


class TestEventCondition(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.condition = {Proposition.parse("in(carrot: f, chest: c)")}
        cls.event = EventCondition(conditions=cls.condition)

    def test_is_triggering(self):
        state = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, chest: c)"),
            Proposition.parse("in(lettuce: f, chest: c)"),
        ])
        assert self.event.is_triggering(state=state)

        state = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, I: I)"),
            Proposition.parse("in(lettuce: f, chest: c)"),
        ])
        assert not self.event.is_triggering(state=state)

    def test_serialization(self):
        data = self.event.serialize()
        event = EventCondition.deserialize(data)
        assert event == self.event

    def test_copy(self):
        event = self.event.copy()
        assert event == self.event
        assert id(event) != id(self.event)


class TestEventAction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rule = Rule.parse("close :: $at(P, r) & $at(chest: c, r) & open(chest: c) -> closed(chest: c)")
        cls.action = Action.parse("close :: $at(P, room: r) & $at(chest: c, room: r) & open(chest: c) -> closed(chest: c)")
        cls.event = EventAction(action=cls.rule)

    def test_is_triggering(self):
        # State should be ignored in a EventAction.
        state = State(KnowledgeBase.default().logic, [
            Proposition.parse("open(chest: c)"),
        ])
        assert self.event.is_triggering(state=state, action=self.action)

        state = State(KnowledgeBase.default().logic, [
            Proposition.parse("closed(chest: c)"),
        ])
        action = Action.parse("close :: open(fridge: c) -> closed(fridge: c)")
        assert not self.event.is_triggering(state=state, action=action)

    def test_serialization(self):
        data = self.event.serialize()
        event = EventAction.deserialize(data)
        assert event == self.event

    def test_copy(self):
        event = self.event.copy()
        assert event == self.event
        assert id(event) != id(self.event)


class TestEventOr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_A_condition = {Proposition.parse("in(carrot: f, chest: c)")}
        cls.event_A = EventCondition(conditions=cls.event_A_condition)

        cls.event_B_action = Rule.parse("close :: open(chest: c) -> closed(chest: c)")
        cls.event_B = EventAction(action=cls.event_B_action)

        cls.event_A_or_B = EventOr(events=(cls.event_A, cls.event_B))

    def test_is_triggering(self):
        open_chest = Action.parse("open :: closed(chest: c) -> open(chest: c)")
        close_chest = Action.parse("close :: open(chest: c) -> closed(chest: c)")
        carrot_in_chest = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, chest: c)"),
        ])
        carrot_in_inventory = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, I: I)"),
        ])

        # A | B
        assert self.event_A.is_triggering(state=carrot_in_chest, action=close_chest)
        assert self.event_B.is_triggering(state=carrot_in_chest, action=close_chest)
        assert self.event_A_or_B.is_triggering(state=carrot_in_chest, action=close_chest)

        # !A | !B
        assert not self.event_A.is_triggering(state=carrot_in_inventory, action=open_chest)
        assert not self.event_B.is_triggering(state=carrot_in_inventory, action=open_chest)
        assert not self.event_A_or_B.is_triggering(state=carrot_in_inventory, action=open_chest)

        # !A | B
        assert not self.event_A.is_triggering(state=carrot_in_inventory, action=close_chest)
        assert self.event_B.is_triggering(state=carrot_in_inventory, action=close_chest)
        assert self.event_A_or_B.is_triggering(state=carrot_in_inventory, action=close_chest)

        # A | !B
        assert self.event_A.is_triggering(state=carrot_in_chest, action=open_chest)
        assert not self.event_B.is_triggering(state=carrot_in_chest, action=open_chest)
        assert self.event_A_or_B.is_triggering(state=carrot_in_chest, action=open_chest)

    def test_serialization(self):
        data = self.event_A_or_B.serialize()
        event = EventOr.deserialize(data)
        assert event == self.event_A_or_B

    def test_copy(self):
        event = self.event_A_or_B.copy()
        assert event == self.event_A_or_B
        assert id(event) != id(self.event_A_or_B)


class TestEventAnd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_A_condition = {Proposition.parse("in(carrot: f, chest: c)")}
        cls.event_A = EventCondition(conditions=cls.event_A_condition)

        cls.event_B_action = Rule.parse("close :: open(chest: c) -> closed(chest: c)")
        cls.event_B = EventAction(action=cls.event_B_action)

        cls.event_A_and_B = EventAnd(events=(cls.event_A, cls.event_B))

    def test_is_triggering(self):
        open_chest = Action.parse("open :: closed(chest: c) -> open(chest: c)")
        close_chest = Action.parse("close :: open(chest: c) -> closed(chest: c)")
        carrot_in_chest = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, chest: c)"),
        ])
        carrot_in_inventory = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, I: I)"),
        ])

        # A & B
        assert self.event_A.is_triggering(state=carrot_in_chest, action=close_chest)
        assert self.event_B.is_triggering(state=carrot_in_chest, action=close_chest)
        assert self.event_A_and_B.is_triggering(state=carrot_in_chest, action=close_chest)

        # !A & !B
        assert not self.event_A.is_triggering(state=carrot_in_inventory, action=open_chest)
        assert not self.event_B.is_triggering(state=carrot_in_inventory, action=open_chest)
        assert not self.event_A_and_B.is_triggering(state=carrot_in_inventory, action=open_chest)

        # !A & B
        assert not self.event_A.is_triggering(state=carrot_in_inventory, action=close_chest)
        assert self.event_B.is_triggering(state=carrot_in_inventory, action=close_chest)
        assert not self.event_A_and_B.is_triggering(state=carrot_in_inventory, action=close_chest)

        # A & !B
        assert self.event_A.is_triggering(state=carrot_in_chest, action=open_chest)
        assert not self.event_B.is_triggering(state=carrot_in_chest, action=open_chest)
        assert not self.event_A_and_B.is_triggering(state=carrot_in_chest, action=open_chest)

    def test_serialization(self):
        data = self.event_A_and_B.serialize()
        event = EventAnd.deserialize(data)
        assert event == self.event_A_and_B

    def test_copy(self):
        event = self.event_A_and_B.copy()
        assert event == self.event_A_and_B
        assert id(event) != id(self.event_A_and_B)


class TestQuest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.carrot_in_chest = {Proposition.parse("in(carrot: f, chest: c)")}
        cls.event_carrot_in_chest = EventCondition(conditions=cls.carrot_in_chest)

        cls.close_chest = Rule.parse("close :: open(chest: c) -> closed(chest: c)")
        cls.event_close_chest = EventAction(action=cls.close_chest)

        cls.event_closing_chest_with_carrot = EventAnd(events=(cls.event_carrot_in_chest, cls.event_close_chest))

        cls.carrot_in_inventory = {Proposition.parse("in(carrot: f, I: I)")}
        cls.event_carrot_in_inventory = EventCondition(conditions=cls.carrot_in_inventory)

        cls.event_closing_chest_without_carrot = EventAnd(events=(cls.event_carrot_in_inventory, cls.event_close_chest))

        cls.eat_carrot = Rule.parse("eat :: in(carrot: f, I: I) -> consumed(carrot: f)")
        cls.event_eat_carrot = EventAction(action=cls.eat_carrot)

        cls.event_closing_chest_whithout_carrot_or_eating_carrot = \
            EventOr(events=(cls.event_closing_chest_without_carrot, cls.event_eat_carrot))

        cls.quest = Quest(win_event=cls.event_closing_chest_with_carrot,
                          fail_event=cls.event_closing_chest_whithout_carrot_or_eating_carrot)

    def test_backward_compatiblity(self):
        # Backward compatibility tests.
        quest = Quest(win_events=[self.event_closing_chest_with_carrot],
                      fail_events=[self.event_closing_chest_without_carrot, self.event_eat_carrot])
        assert quest == self.quest

        quest = Quest([self.event_closing_chest_with_carrot],
                      [self.event_closing_chest_without_carrot, self.event_eat_carrot])
        assert quest == self.quest

    def test_is_winning_or_failing(self):
        close_chest = Action.parse("close :: open(chest: c) -> closed(chest: c)")
        eat_carrot = Action.parse("eat :: in(carrot: f, I: I) -> consumed(carrot: f)")
        carrot_in_chest = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, chest: c)"),
        ])
        carrot_in_inventory = State(KnowledgeBase.default().logic, [
            Proposition.parse("in(carrot: f, I: I)"),
        ])

        assert self.quest.is_winning(state=carrot_in_chest, action=close_chest)
        assert not self.quest.is_failing(state=carrot_in_chest, action=close_chest)
        assert self.quest.is_failing(state=carrot_in_inventory, action=close_chest)
        assert not self.quest.is_winning(state=carrot_in_inventory, action=close_chest)
        assert self.quest.is_failing(state=carrot_in_inventory, action=eat_carrot)
        assert not self.quest.is_winning(state=carrot_in_inventory, action=eat_carrot)
        assert self.quest.is_failing(state=carrot_in_chest, action=eat_carrot)
        assert not self.quest.is_winning(state=carrot_in_chest, action=eat_carrot)

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

        def _rule_to_skip(rule):
            # Examine, look and inventory shouldn't be used for chaining.
            if rule.name.startswith("look"):
                return True

            if rule.name.startswith("inventory"):
                return True

            if rule.name.startswith("examine"):
                return True

            return False

        for max_depth in range(1, 3):
            for rule in KnowledgeBase.default().rules.values():
                if _rule_to_skip(rule):
                    continue

                options = ChainingOptions()
                options.backward = True
                options.max_depth = max_depth
                options.max_length = max_depth
                options.create_variables = True
                options.rules_per_depth = [[rule]]
                options.restricted_types = {"r"}
                chain = sample_quest(world.state, options)

                # Build the quest by providing the actions.
                actions = chain.actions
                assert len(actions) == max_depth, rule.name

                quest = Quest(win_event=EventCondition(actions=actions))
                tmp_world = World.from_facts(chain.initial_state.facts)

                state = tmp_world.state
                for action in actions:
                    assert not quest.is_winning(state)
                    state.apply(action)

                assert quest.is_winning(state)

                # Build the quest by only providing the winning conditions.
                quest = Quest(win_event=EventCondition(conditions=actions[-1].postconditions))
                tmp_world = World.from_facts(chain.initial_state.facts)

                state = tmp_world.state
                for action in actions:
                    assert not quest.is_winning(state)
                    state.apply(action)

                assert quest.is_winning(state)


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
        cls.walkthrough = commands

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
                          "inventory", "examine"}
        assert set(self.game.verbs) == expected_verbs

    def test_walkthrough(self):
        assert self.game.walkthrough == self.walkthrough

    def test_command_templates(self):
        expected_templates = {
            'close {c}', 'close {d}', 'drop {o}', 'eat {f}', 'examine {d}',
            'examine {o}', 'examine {t}', 'go east', 'go north', 'go south',
            'go west', 'insert {o} into {c}', 'inventory', 'lock {c} with {k}',
            'lock {d} with {k}', 'look', 'open {c}', 'open {d}', 'put {o} on {s}',
            'take {o}', 'take {o} from {c}', 'take {o} from {s}',
            'unlock {c} with {k}', 'unlock {d} with {k}'
        }
        assert set(self.game.command_templates) == expected_templates

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
        cls.game = DATA["game"]
        cls.win_event = DATA["quest"].win_event
        cls.eating_carrot = DATA["eating_carrot"]
        cls.onion_eaten = DATA["onion_eaten"]

    def test_triggering_policy(self):
        event = EventProgression(self.win_event, KnowledgeBase.default())

        state = self.game.world.state.copy()
        for action in event.triggering_policy:
            assert not event.done
            assert not event.triggered
            assert not event.untriggerable
            state.apply(action)
            event.update(action=action, state=state)

        assert event.triggering_policy == ()
        assert event.done
        assert event.triggered
        assert not event.untriggerable

        event = EventProgression(self.win_event, KnowledgeBase.default())
        state = self.game.world.state.copy()

        expected_actions = self.eating_carrot.actions
        for i, action in enumerate(expected_actions):
            state.apply(action)
            event.update(action=action, state=state)

        for action in event.triggering_policy:
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
        event = EventProgression(self.win_event, KnowledgeBase.default())

        state = self.game.world.state.copy()
        for action in self.eating_carrot.actions:
            assert event.triggering_policy != ()
            assert not event.done
            assert not event.triggered
            assert not event.untriggerable
            state.apply(action)
            event.update(action=action, state=state)

        for action in self.onion_eaten.actions:
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
        cls.game = DATA["game"]
        cls.quest = DATA["quest"]
        cls.eating_carrot = DATA["eating_carrot"]
        cls.onion_eaten = DATA["onion_eaten"]
        cls.closing_chest_without_carrot = DATA["closing_chest_without_carrot"]

    def _apply_actions_to_quest(self, actions, quest, state=None):
        state = state or self.game.world.state.copy()
        for action in actions:
            assert not quest.done
            state.apply(action)
            quest.update(action, state)

        return state

    def test_completed(self):
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        self._apply_actions_to_quest(self.quest.win_event.events[0].actions, quest)
        assert quest.done
        assert quest.completed and not quest.failed
        assert quest.winning_policy is None

        # Alternative winning strategy.
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        self._apply_actions_to_quest(self.quest.win_event.events[1].actions, quest)
        assert quest.done
        assert quest.completed and not quest.failed
        assert quest.winning_policy is None

    def test_failed(self):
        # onion_eaten -> eating_carrot != eating_carrot -> onion_eaten
        # Eating the carrot *after* eating the onion causes the game to be lost.
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        state = self._apply_actions_to_quest(self.onion_eaten.actions, quest)
        self._apply_actions_to_quest(self.eating_carrot.actions, quest, state)
        assert quest.done
        assert not quest.completed and quest.failed
        assert quest.winning_policy is None

        # Eating the carrot *before* eating the onion does not lose the game,
        # causes the game to be unfinishable.
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        state = self._apply_actions_to_quest(self.eating_carrot.actions, quest)
        self._apply_actions_to_quest(self.onion_eaten.actions, quest, state)
        assert quest.done and quest.unfinishable
        assert not quest.completed and not quest.failed

        quest = QuestProgression(self.quest, KnowledgeBase.default())
        self._apply_actions_to_quest(self.closing_chest_without_carrot.actions, quest)
        assert quest.done
        assert not quest.completed and quest.failed
        assert quest.winning_policy is None

    def test_winning_policy(self):
        kb = KnowledgeBase.default()
        quest = QuestProgression(self.quest, kb)
        self._apply_actions_to_quest(quest.winning_policy, quest)
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None

        # Winning policy should be the shortest one leading to a winning event.
        state = self.game.world.state.copy()
        quest = QuestProgression(self.quest, KnowledgeBase.default())
        for i, action in enumerate(self.quest.win_event.events[1].actions):
            if i < 2:
                assert set(quest.winning_policy).issubset(set(self.quest.win_event.events[0].actions))
                assert not set(quest.winning_policy).issubset(set(self.quest.win_event.events[1].actions))
            else:
                # After opening the chest and taking the onion,
                # the alternative winning event becomes the shortest one to complete.
                assert quest.winning_policy == self.quest.win_event.events[1].actions[i:]

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
        cls.game = DATA["game"]
        cls.quest1 = DATA["quest1"]
        cls.quest2 = DATA["quest2"]
        cls.eating_carrot = DATA["eating_carrot"]
        cls.onion_eaten = DATA["onion_eaten"]
        cls.knife_on_counter = DATA["knife_on_counter"]

    def test_completed(self):
        game = GameProgression(self.game)
        for action in self.quest1.win_event.events[0].actions + self.quest2.win_event.events[0].actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert game.completed and not game.failed
        assert game.winning_policy is None

        # Alternative quest1 solution
        game = GameProgression(self.game)
        for action in self.quest1.win_event.events[1].actions + self.quest2.win_event.events[0].actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert game.completed and not game.failed
        assert game.winning_policy is None

    def test_failed(self):
        game = GameProgression(self.game)

        # Completing quest2 but failing quest 1.
        for action in self.knife_on_counter.actions:
            game.update(action)

        assert not game.quest_progressions[0].done
        assert game.quest_progressions[1].done
        assert game.quest_progressions[1].completed
        assert not game.done
        assert not game.completed and not game.failed
        assert game.winning_policy is not None

        for action in self.onion_eaten.actions + self.eating_carrot.actions:
            game.update(action)

        assert game.done
        assert game.quest_progressions[0].done
        assert game.quest_progressions[0].failed
        assert not game.completed and game.failed
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
        M.set_walkthrough(commands)  # TODO: redundant!
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
        M.set_walkthrough(commands)  # TODO: redundant!
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
        # quest3 = M.new_quest_using_commands(commands[0] + commands[1] + commands[2])
        winning_facts = [M.new_fact("in", lettuce, chest),
                         M.new_fact("in", carrot, chest),
                         M.new_fact("closed", chest)]
        quest3 = Quest(win_event=EventCondition(winning_facts))
        quest3.desc = "Put the lettuce and the carrot into the chest before closing it."

        M.quests = [quest1, quest2, quest3]
        M.set_walkthrough(commands[0] + commands[1] + commands[2])
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
