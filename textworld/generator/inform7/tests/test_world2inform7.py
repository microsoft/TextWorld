# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import itertools

import textworld
from textworld import g_rng
from textworld.utils import make_temp_directory

from textworld.generator import data
from textworld.generator import World, Quest
from textworld.generator import compile_game
from textworld.generator import make_small_map, make_grammar, make_game_with
from textworld.generator.chaining import ChainingOptions, sample_quest
from textworld.logic import Proposition


def test_quest_winning_condition_go():
    M = textworld.GameMaker()

    # R1 -- R2 -- R3
    R1 = M.new_room("West room")
    R2 = M.new_room("Center room")
    R3 = M.new_room("East room")
    M.set_player(R1)

    M.connect(R1.east, R2.west)
    M.connect(R2.east, R3.west)

    M.set_quest_from_commands(["go east", "go east"])

    game = M.build()
    game_name = "test_quest_winning_condition_go"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)

        env = textworld.start(game_file)
        env.reset()
        game_state, _, done = env.step("go east")
        assert not done
        assert not game_state.has_won

        game_state, _, done = env.step("go east")
        assert done
        assert game_state.has_won


def test_quest_winning_condition():
    g_rng.set_seed(2018)
    map_ = make_small_map(n_rooms=5, possible_door_states=["open"])
    world = World.from_map(map_)

    for rule in data.get_rules().values():
        options = ChainingOptions()
        options.backward = True
        options.max_depth = 1
        options.create_variables = True
        options.rules_per_depth = [[rule]]
        options.restricted_types = {"r"}
        chain = sample_quest(world.state, options)
        assert len(chain.actions) > 0, rule.name
        quest = Quest(chain.actions)

        # Set the initial state required for the quest.
        tmp_world = World.from_facts(chain.initial_state.facts)
        game = make_game_with(tmp_world, [quest], make_grammar({}))

        if tmp_world.player_room is None:
            # Randomly place the player in the world since
            # the action doesn't care about where the player is.
            tmp_world.set_player_room()

        game_name = "test_quest_winning_condition_" + rule.name.replace("/", "_")
        with make_temp_directory(prefix=game_name) as tmpdir:
            game_file = compile_game(game, game_name, games_folder=tmpdir)

            env = textworld.start(game_file)
            env.reset()
            game_state, _, done = env.step("look")
            assert not done
            assert not game_state.has_won

            game_state, _, done = env.step(quest.commands[0])
            assert done
            assert game_state.has_won


def test_quest_losing_condition():
    g_rng.set_seed(2018)
    M = textworld.GameMaker()

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

    failing_conditions = (Proposition("eaten", [carrot.var]),)
    quest = M.set_quest_from_commands(commands)
    quest.set_failing_conditions(failing_conditions)
    game = M.build()

    game_name = "test_quest_losing_condition"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)

        env = textworld.start(game_file)
        env.reset()
        # Make sure we do not rely on the quest progression to
        # determine if the game was lost.
        assert not env._compute_intermediate_reward

        game_state, _, done = env.step("eat carrot")
        assert done
        assert game_state.has_lost
        assert not game_state.has_won


def test_names_disambiguation():
    M = textworld.GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    apple = M.new(type="o", name="apple")
    orange = M.new(type="o", name="orange")
    tasty_apple = M.new(type="o", name="tasty apple")
    tasty_orange = M.new(type="o", name="tasty orange")
    room.add(apple, orange, tasty_apple, tasty_orange)

    game = M.build()
    game_name = "test_names_disambiguation"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)
        env = textworld.start(game_file)
        env.reset()
        game_state, _, done = env.step("take tasty apple")
        assert "tasty apple" in game_state.inventory
        game_state, _, done = env.step("take tasty orange")
        assert "tasty orange" in game_state.inventory

        env.reset()
        game_state, _, done = env.step("take orange")
        assert "tasty orange" not in game_state.inventory
        assert "orange" in game_state.inventory

        game_state, _, done = env.step("take tasty")
        assert "?" in game_state.feedback  # Disambiguation question.
        game_state, _, done = env.step("apple")
        assert "tasty orange" not in game_state.inventory
        assert "tasty apple" in game_state.inventory
        assert "tasty apple" not in game_state.description


def test_take_all_and_variants():
    M = textworld.GameMaker()

    # Empty room.
    room = M.new_room("room")
    M.set_player(room)

    game = M.build()
    game_name = "test_take_all_and_variants"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)
        env = textworld.start(game_file)
        env.reset()

        variants_to_test = itertools.product(["take", "get", "pick up"],
                                             ["all", "everything", "each"])
        for command in variants_to_test:
            game_state, _, done = env.step(" ".join(command))
            assert game_state.feedback.strip() == "You have to be more specific!"

    # Multiple objects to take.
    red_ball = M.new(type="o", name="red ball")
    blue_ball = M.new(type="o", name="blue ball")
    room.add(red_ball, blue_ball)

    game = M.build()
    game_name = "test_take_all_and_variants2"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)
        env = textworld.start(game_file)
        env.reset()

        game_state, _, done = env.step("take all ball")
        assert "red ball: Taken." in game_state.feedback
        assert "blue ball: Taken." in game_state.feedback
        assert "red ball" in game_state.inventory
        assert "blue ball" in game_state.inventory
