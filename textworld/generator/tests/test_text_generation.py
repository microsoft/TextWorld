#!/usr/bin/env python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np

import textworld
from textworld import g_rng

import textworld.agents
from textworld.generator import World
from textworld.logic import Variable, Proposition


def test_used_names_is_updated(verbose=False):
    # Make generation throughout the framework reproducible.
    g_rng.set_seed(1234)

    # Generate a map that's shape in a cross with room0 in the middle.
    P = Variable('P')
    r = Variable('r_0', 'r')
    k1 = Variable('k_1', 'k')
    k2 = Variable('k_2', 'k')
    c1 = Variable('c_1', 'c')
    c2 = Variable('c_2', 'c')
    facts = [Proposition('at', [P, r]),
             Proposition('at', [k1, r]),
             Proposition('at', [k2, r]),
             Proposition('at', [c1, r]),
             Proposition('at', [c2, r]),
             Proposition('match', [k1, c1]),
             Proposition('match', [k2, c2])]
    world = World.from_facts(facts)
    world.set_player_room()  # Set start room to the middle one.
    world.populate_room(10, world.player_room)  # Add objects to the starting room.

    # Generate the world representation.
    grammar = textworld.generator.make_grammar({}, rng=np.random.RandomState(42))

    game = textworld.generator.make_game_with(world, [], grammar)
    for entity_infos in game.infos.values():
        if entity_infos.name is None:
            continue

        assert entity_infos.name in grammar.used_names


def test_blend_instructions(verbose=False):
    # Make generation throughout the framework reproducible.
    g_rng.set_seed(1234)

    M = textworld.GameMaker()
    r1 = M.new_room()
    r2 = M.new_room()
    M.set_player(r1)

    path = M.connect(r1.north, r2.south)
    path.door = M.new(type="d", name="door")
    M.add_fact("locked", path.door)
    key = M.new(type="k", name="key")
    M.add_fact("match", key, path.door)
    r1.add(key)

    quest = M.set_quest_from_commands(["take key", "unlock door with key", "open door", "go north",
                                       "close door", "lock door with key", "drop key"])

    game = M.build()

    grammar1 = textworld.generator.make_grammar({"blend_instructions": False},
                                                rng=np.random.RandomState(42))

    grammar2 = textworld.generator.make_grammar({"blend_instructions": True},
                                                rng=np.random.RandomState(42))

    quest.desc = None
    game.change_grammar(grammar1)
    quest1 = quest.copy()
    quest.desc = None
    game.change_grammar(grammar2)
    quest2 = quest.copy()
    assert len(quest1.desc) > len(quest2.desc)


def test_do_not_overwrite_entity_desc(verbose=False):
    # Make generation throughout the framework reproducible.
    g_rng.set_seed(1234)

    M = textworld.GameMaker()
    r1 = M.new_room()
    M.set_player(r1)

    key = M.new(type="k", name="key", desc="This is a skeleton key.")
    r1.add(key)

    quest = M.set_quest_from_commands(["take key"])
    quest.desc = "Find a valuable object."

    M.build()
    assert key.infos.desc == "This is a skeleton key."
    assert quest.desc == "Find a valuable object."


if __name__ == "__main__":
    test_blend_instructions(verbose=True)
