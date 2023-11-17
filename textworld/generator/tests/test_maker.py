# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np
import numpy.testing as npt

import textworld

from textworld.utils import make_temp_directory

from textworld.generator.maker import GameMaker
from textworld.generator.maker import ExitAlreadyUsedError
from textworld.generator.maker import FailedConstraintsError
from textworld.generator.maker import MissingPlayerError
from textworld.generator.maker import PlayerAlreadySetError


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

    options = textworld.GameOptions()
    options.path = folder
    game_file = textworld.generator.compile_game(game, options)
    return game_file


def test_missing_player():
    M = GameMaker()
    M.new_room()
    npt.assert_raises(MissingPlayerError, M.build)


def test_player_set_twice():
    M = GameMaker()
    R1 = M.new_room()
    M.set_player(R1)
    R2 = M.new_room()
    npt.assert_raises(PlayerAlreadySetError, M.set_player, R2)


def test_already_exit_already_linked():
    M = GameMaker()
    R1 = M.new_room()
    R2 = M.new_room()
    R3 = M.new_room()

    M.connect(R1.east, R2.west)
    npt.assert_raises(ExitAlreadyUsedError, M.connect, R1.east, R3.west)


def test_expecting_door_entity_in_path():
    M = GameMaker()
    R1 = M.new_room()
    R2 = M.new_room()

    path = M.connect(R1.east, R2.west)
    npt.assert_raises(TypeError, setattr, path.door, 'dummy')


def test_adding_the_same_object_multiple_times():
    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)
    container1 = M.new('c', name='container')
    container2 = M.new('c', name="another container")
    room.add(container1, container2)

    obj = M.new('o')
    container1.add(obj)
    container2.add(obj)
    npt.assert_raises(FailedConstraintsError, M.validate)


def test_adding_objects():
    M = GameMaker()

    objs = [M.new('o') for _ in range(5)]  # Objects to be added.
    container = M.new('c')
    container.add(*objs)
    assert all(f.name == "in" for f in container.facts)

    objs = [M.new('o') for _ in range(5)]  # Objects to be added.
    room = M.new('r')
    room.add(*objs)
    assert all(f.name == "at" for f in room.facts)

    objs = [M.new('o') for _ in range(5)]  # Objects to be added.
    supporter = M.new('s')
    supporter.add(*objs)
    assert all(f.name == "on" for f in supporter.facts)


def test_making_a_small_game(play_the_game=False):
    M = GameMaker()
    # Create a 'bedroom' room.
    R1 = M.new_room("bedroom")
    M.set_player(R1)

    # Add a second room to the east of R1.
    R2 = M.new_room()            # Generated name
    path = M.connect(R1.east, R2.west)  # Undirected path

    # Add a closed door between R1 and R2.
    door = M.new_door(path, name='glass door')
    door.add_property("locked")

    # Put a matching key for the door on R1's floor.
    key = M.new(type='k', name='rusty key')
    M.add_fact("match", key, door)
    R1.add(key)

    # Add a closed chest in R2.
    chest = M.new(type='c', name='chest')
    chest.add_property("closed")
    R2.add(chest)

    # Add a 3 random portable objects in the chest.
    objs = [M.new(type='o') for _ in range(3)]
    chest.add(*objs)

    # Add 3 food objects in the player's inventory.
    foods = [M.new(type='f') for _ in range(3)]
    M.inventory.add(*foods)

    game = M.build()
    assert "GameMaker" in game.metadata["desc"]

    with make_temp_directory(prefix="test_making_a_small_game") as tmpdir:
        game_file = _compile_game(game, folder=tmpdir)

        if play_the_game:
            textworld.play(game_file)


def test_record_quest_from_commands(play_the_game=False):
    M = GameMaker()

    # The goal
    commands = ["go east", "insert ball into chest"]

    # Create a 'bedroom' room.
    R1 = M.new_room("bedroom")
    R2 = M.new_room("kitchen")
    M.set_player(R1)

    path = M.connect(R1.east, R2.west)
    path.door = M.new(type='d', name='wooden door')
    path.door.add_property("open")

    ball = M.new(type='o', name='ball')
    M.inventory.add(ball)

    # Add a closed chest in R2.
    chest = M.new(type='c', name='chest')
    chest.add_property("open")
    R2.add(chest)

    M.set_quest_from_commands(commands)
    game = M.build()

    with make_temp_directory(prefix="test_record_quest_from_commands") as tmpdir:
        game_file = _compile_game(game, folder=tmpdir)

        if play_the_game:
            textworld.play(game_file)
        else:
            agent = textworld.agents.WalkthroughAgent(commands)
            textworld.play(game_file, agent=agent, silent=True)


def test_manually_defined_objective():
    M = GameMaker()

    # Create a 'bedroom' room.
    R1 = M.new_room("bedroom")
    M.set_player(R1)

    game = M.build()
    game.objective = "There's nothing much to do in here."

    with make_temp_directory(prefix="test_manually_defined_objective") as tmpdir:
        game_file = M.compile(tmpdir)

        env = textworld.start(game_file, request_infos=textworld.EnvInfos(objective=True))
        state = env.reset()
        assert state["objective"] == "There's nothing much to do in here."


if __name__ == "__main__":
    # test_making_a_small_game(play_the_game=True)
    test_record_quest_from_commands(play_the_game=True)
