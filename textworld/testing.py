# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import sys
import contextlib

import numpy as np

import textworld
from textworld.generator.game import Event, Quest
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


def _compile_test_game(game, options: GameOptions):
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

    game_file = textworld.generator.compile_game(game, options)
    return game_file


def build_and_compile_no_quest_game(options: GameOptions):
    M = textworld.GameMaker()

    room = M.new_room()
    M.set_player(room)
    item = M.new(type="o")
    room.add(item)
    game = M.build()

    game_file = _compile_test_game(game, options)
    return game, game_file


def build_and_compile_game(options: GameOptions):
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
    game_file = _compile_test_game(game, options)
    return game, game_file
