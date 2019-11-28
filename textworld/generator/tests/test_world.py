# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy.testing as npt

from textworld.generator import World
from textworld.logic import Proposition, Variable
from textworld.generator.graph_networks import reverse_direction

from textworld.generator.world import connect
from textworld.generator.world import NoFreeExitError


def test_automatically_positioning_rooms():
    P = Variable("P")
    r1 = Variable("Room1", "r")
    r2 = Variable("Room2", "r")
    d = Variable("door", "d")
    facts = [Proposition("at", [P, r1])]
    world = World.from_facts(facts)
    assert len(world.rooms) == 1
    assert len(world.find_room_by_id(r1.name).exits) == 0

    world.add_fact(Proposition("link", [r1, d, r2]))
    assert len(world.rooms) == 2
    r1_entity = world.find_room_by_id(r1.name)
    r2_entity = world.find_room_by_id(r2.name)
    assert len(r1_entity.exits) == 1
    assert len(r2_entity.exits) == 1

    assert list(r1_entity.exits.keys())[0] == reverse_direction(list(r2_entity.exits.keys())[0])


def test_cannot_automatically_positioning_rooms():
    P = Variable("P")
    r0 = Variable("Room0", "r")
    r1 = Variable("Room1", "r")
    r2 = Variable("Room2", "r")
    r3 = Variable("Room3", "r")
    r4 = Variable("Room4", "r")
    r5 = Variable("Room5", "r")
    d = Variable("door", "d")

    facts = [Proposition("at", [P, r0])]
    facts.extend(connect(r0, 'north', r1))
    facts.extend(connect(r0, 'east', r2))
    facts.extend(connect(r0, 'south', r3))
    facts.extend(connect(r0, 'west', r4))

    world = World.from_facts(facts)
    npt.assert_raises(NoFreeExitError, world.add_fact, Proposition("link", [r0, d, r5]))


def test_get_all_objects_in():
    P = Variable("P")
    room = Variable("room", "r")
    chest = Variable("chest", "c")
    obj = Variable("obj", "o")
    facts = [Proposition("at", [P, room]),
             Proposition("at", [chest, room]),
             Proposition("in", [obj, chest]),
             Proposition("closed", [chest])]

    world = World.from_facts(facts)
    objects = world.get_all_objects_in(world.player_room)
    assert obj in world.objects
    assert obj in objects


def test_get_visible_objects_in():
    P = Variable("P")
    room = Variable("room", "r")
    chest = Variable("chest", "c")
    obj = Variable("obj", "o")

    # Closed chest.
    facts = [Proposition("at", [P, room]),
             Proposition("at", [chest, room]),
             Proposition("in", [obj, chest]),
             Proposition("closed", [chest])]

    world = World.from_facts(facts)
    objects = world.get_visible_objects_in(world.player_room)
    assert obj in world.objects
    assert obj not in objects

    # Open chest.
    facts = [Proposition("at", [P, room]),
             Proposition("at", [chest, room]),
             Proposition("in", [obj, chest]),
             Proposition("open", [chest])]

    world = World.from_facts(facts)
    objects = world.get_visible_objects_in(world.player_room)
    assert obj in world.objects
    assert obj in objects


def test_get_objects_in_inventory():
    P = Variable("P")
    I = Variable("I")
    room = Variable("room", "r")
    obj = Variable("obj", "o")

    # Closed chest.
    facts = [Proposition("at", [P, room]),
             Proposition("in", [obj, I])]

    world = World.from_facts(facts)
    objects = world.get_objects_in_inventory()
    assert obj in world.objects
    assert obj in objects


def test_populate_room_with():
    # setup
    P = Variable('P')
    I = Variable('I')
    room = Variable('room', 'r')
    facts = [Proposition('at', [P, room])]

    world = World.from_facts(facts)

    # test
    obj = Variable('obj', 'o')
    world.populate_room_with(objects=[obj], room=room)

    assert obj in world.objects
    assert (Proposition('at', [obj, room]) in world.facts or Proposition('in', [obj, I]) in world.facts)


def test_populate_with():
    # setup
    P = Variable('P')
    I = Variable('I')
    room = Variable('room', 'r')
    facts = [Proposition('at', [P, room])]

    world = World.from_facts(facts)

    # test
    obj = Variable('obj', 'o')
    world.populate_with(objects=[obj])

    assert obj in world.objects
    assert (Proposition('at', [obj, room]) in world.facts or Proposition('in', [obj, I]) in world.facts)
