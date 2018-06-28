# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy.testing as npt

from textworld.generator import make_world, make_small_map, make_world_with

from textworld.logic import Variable, Proposition


def test_make_world_no_rng():
    world = make_world(1)
    assert world is not None


def test_make_small_map_too_big():
    # small maps have max size
    npt.assert_raises(ValueError, make_small_map, n_rooms=6)


def test_make_small_map():
    world = make_small_map(n_rooms=4)
    assert world is not None


def test_make_world_with():
    r1 = Variable("r_0", "r")
    P = Variable('P')
    world = make_world_with(rooms=[r1])
    assert Proposition('at', [P, r1]) in world.facts
