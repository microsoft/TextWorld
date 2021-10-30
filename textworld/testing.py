# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import sys
import contextlib

from typing import Tuple, Optional

import numpy as np

import textworld
from textworld.generator.game import Event, Quest, Game
from textworld.generator.game import EventAction, EventCondition, EventOr, EventAnd
from textworld.generator.game import GameOptions


@contextlib.contextmanager
def capture_stdout():
    # Capture stdout.
    stdout_bak = sys.stdout
    sys.stdout = out = io.StringIO()
    try:
        yield out
    finally:
        # Restore stdout
        sys.stdout = stdout_bak


def _compile_test_game(game, options: GameOptions) -> str:
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
    grammar = textworld.generator.make_grammar(grammar_flags, rng=rng_grammar, kb=options.kb)
    game.change_grammar(grammar)

    game_file = textworld.generator.compile_game(game, options)
    return game_file


def build_and_compile_no_quest_game(options: GameOptions) -> Tuple[Game, str]:
    M = textworld.GameMaker()

    room = M.new_room()
    M.set_player(room)
    item = M.new(type="o")
    room.add(item)
    game = M.build()

    game_file = _compile_test_game(game, options)
    return game, game_file


def build_game(options: GameOptions) -> Game:
    M = textworld.GameMaker()

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

    quest1_cmds = ["go east", "insert carrot into chest"]
    carrot_in_chest = M.new_event_using_commands(quest1_cmds)
    eating_carrot = Event(conditions={M.new_fact("eaten", carrot)})
    quest1 = Quest(win_events=[carrot_in_chest],
                   fail_events=[eating_carrot],
                   reward=2)

    quest2_cmds = quest1_cmds + ["close chest"]
    quest2_actions = M.new_event_using_commands(quest2_cmds).actions
    chest_closed_with_carrot = Event(
        conditions={
            M.new_fact("in", carrot, chest),
            M.new_fact("closed", chest)
        },
        actions=quest2_actions)

    quest2 = Quest(win_events=[chest_closed_with_carrot],
                   fail_events=[eating_carrot])

    M.quests = [quest1, quest2]
    M.set_walkthrough(quest2_cmds)
    game = M.build()
    return game


def build_and_compile_game(options: GameOptions) -> Tuple[Game, str]:
    game = build_game(options)
    game_file = _compile_test_game(game, options)
    return game, game_file


def build_complex_test_game(options: Optional[GameOptions] = None):
    M = textworld.GameMaker(options)

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
        ]),
        reward=3,
    )

    knife_on_counter = EventCondition(conditions={M.new_fact("on", knife, counter)})

    quest2 = Quest(
        win_event=knife_on_counter,
        reward=5,
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
