# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import itertools

import numpy as np

import textworld
from textworld import g_rng
from textworld.utils import make_temp_directory

from textworld.core import EnvInfos
from textworld.generator.data import KnowledgeBase
from textworld.generator import World, Quest, Event
from textworld.generator import compile_game
from textworld.generator import make_small_map, make_grammar, make_game_with
from textworld.generator.chaining import ChainingOptions, sample_quest


def _compile_game(game, path):
    options = textworld.GameOptions()
    options.path = path
    return compile_game(game, options)


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
        game_file = _compile_game(game, path=tmpdir)

        env = textworld.start(game_file)
        env.reset()
        game_state, _, done = env.step("go east")
        assert not done
        assert not game_state.won

        game_state, _, done = env.step("go east")
        assert done
        assert game_state.won


def test_quest_winning_condition():
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

    for rule in KnowledgeBase.default().rules.values():
        if _rule_to_skip(rule):
            continue

        options = ChainingOptions()
        options.backward = True
        options.max_depth = 1
        options.create_variables = True
        options.rules_per_depth = [[rule]]
        options.restricted_types = {"r"}
        chain = sample_quest(world.state, options)
        assert len(chain.actions) > 0, rule.name
        event = Event(chain.actions)
        quest = Quest(win_events=[event])

        # Set the initial state required for the quest.
        tmp_world = World.from_facts(chain.initial_state.facts)
        game = make_game_with(tmp_world, [quest], make_grammar({}))

        if tmp_world.player_room is None:
            # Randomly place the player in the world since
            # the action doesn't care about where the player is.
            tmp_world.set_player_room()

        game_name = "test_quest_winning_condition_" + rule.name.replace("/", "_")
        with make_temp_directory(prefix=game_name) as tmpdir:
            game_file = _compile_game(game, path=tmpdir)

            env = textworld.start(game_file)
            env.reset()
            game_state, _, done = env.step("look")
            assert not done
            assert not game_state.won

            game_state, _, done = env.step(event.commands[0])
            assert done
            assert game_state.won


def test_quest_with_multiple_winning_and_losing_conditions():
    g_rng.set_seed(2018)
    M = textworld.GameMaker()

    # Create a 'bedroom' room.
    R1 = M.new_room("bedroom")
    R2 = M.new_room("kitchen")
    M.set_player(R1)

    path = M.connect(R1.east, R2.west)
    path.door = M.new(type='d', name='wooden door')
    path.door.add_property("open")

    carrot = M.new(type='f', name='carrot')
    lettuce = M.new(type='f', name='lettuce')
    M.inventory.add(carrot)
    M.inventory.add(lettuce)

    # Add a closed chest in R2.
    chest = M.new(type='c', name='chest')
    chest.add_property("open")
    R2.add(chest)

    # The goal
    quest = Quest(win_events=[Event(conditions={M.new_fact("in", carrot, chest),
                                                M.new_fact("closed", chest)}),
                              Event(conditions={M.new_fact("eaten", lettuce)})],
                  fail_events=[Event(conditions={M.new_fact("in", lettuce, chest),
                                                 M.new_fact("closed", chest)}),
                               Event(conditions={M.new_fact("eaten", carrot)})])
    M.quests = [quest]
    game = M.build()

    game_name = "test_quest_with_multiple_winning_and_losing_conditions"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)

        env = textworld.start(game_file)

        # Failing - 1
        env.reset()
        game_state, _, done = env.step("eat carrot")
        assert done
        assert game_state.lost
        assert not game_state.won

        # Failing - 2
        env.reset()
        game_state, _, done = env.step("go east")
        assert not done
        game_state, _, done = env.step("insert lettuce into chest")
        assert not done
        game_state, _, done = env.step("close chest")
        assert done
        assert game_state.lost
        assert not game_state.won

        # Failing - 1
        env.reset()
        game_state, _, done = env.step("eat lettuce")
        assert done
        assert not game_state.lost
        assert game_state.won

        # Winning - 2
        env.reset()
        game_state, _, done = env.step("go east")
        assert not done
        game_state, _, done = env.step("insert carrot into chest")
        assert not done
        game_state, _, done = env.step("close chest")
        assert done
        assert not game_state.lost
        assert game_state.won


def test_cannot_win_or_lose_a_quest_twice():
    g_rng.set_seed(2018)
    M = textworld.GameMaker()

    # Create a 'bedroom' room.
    R1 = M.new_room("bedroom")
    R2 = M.new_room("kitchen")
    M.set_player(R1)

    path = M.connect(R1.east, R2.west)
    path.door = M.new(type='d', name='wooden door')
    path.door.add_property("open")

    carrot = M.new(type='f', name='carrot')
    lettuce = M.new(type='f', name='lettuce')
    M.inventory.add(carrot)
    M.inventory.add(lettuce)

    # Add a closed chest in R2.
    chest = M.new(type='c', name='chest')
    chest.add_property("open")
    R2.add(chest)

    # The goals
    event_carrot_in_closed_chest = Event(conditions={M.new_fact("in", carrot, chest),
                                                     M.new_fact("closed", chest)})
    event_drop_carrot_R1 = Event(conditions={M.new_fact("at", carrot, R1)})
    event_drop_carrot_R2 = Event(conditions={M.new_fact("at", carrot, R2)})

    quest1 = Quest(win_events=[event_carrot_in_closed_chest],
                   fail_events=[event_drop_carrot_R1, event_drop_carrot_R2])

    event_lettuce_in_closed_chest = Event(conditions={M.new_fact("in", lettuce, chest),
                                                      M.new_fact("closed", chest)})
    event_drop_lettuce_R1 = Event(conditions={M.new_fact("at", lettuce, R1)})
    event_drop_lettuce_R2 = Event(conditions={M.new_fact("at", lettuce, R2)})

    quest2 = Quest(win_events=[event_lettuce_in_closed_chest],
                   fail_events=[event_drop_lettuce_R1, event_drop_lettuce_R2])

    M.quests = [quest1, quest2]
    game = M.build()

    game_name = "test_cannot_win_or_lose_a_quest_twice"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)

        env = textworld.start(game_file)

        # Complete quest1 then fail it.
        env.reset()
        game_state, score, done = env.step("go east")
        assert score == 0
        game_state, score, done = env.step("insert carrot into chest")
        assert score == 0
        game_state, score, done = env.step("close chest")
        assert score == 1
        assert not done
        game_state, score, done = env.step("open chest")

        # Re-completing quest1 doesn't award more points.
        game_state, score, done = env.step("close chest")
        assert score == 1
        assert not done

        game_state, score, done = env.step("open chest")
        game_state, score, done = env.step("take carrot from chest")
        game_state, score, done = env.step("drop carrot")
        assert score == 1
        assert not done

        # Then fail quest2.
        game_state, score, done = env.step("drop lettuce")
        assert done
        assert game_state.lost
        assert not game_state.won

        env.reset()
        game_state, score, done = env.step("go east")
        game_state, score, done = env.step("insert carrot into chest")
        game_state, score, done = env.step("insert lettuce into chest")
        game_state, score, done = env.step("close chest")
        assert score == 2
        assert done
        assert not game_state.lost
        assert game_state.won


def test_disambiguation_questions():
    M = textworld.GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    tasty_apple = M.new(type="o", name="tasty apple")
    tasty_orange = M.new(type="o", name="tasty orange")
    room.add(tasty_apple, tasty_orange)

    game = M.build()
    game_name = "test_names_disambiguation"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file, EnvInfos(description=True, inventory=True))

        game_state = env.reset()
        previous_inventory = game_state.inventory
        previous_description = game_state.description

        game_state, _, _ = env.step("take tasty")
        assert "?" in game_state.feedback  # Disambiguation question.

        # When there is a question in Inform7, the next string sent to the game
        # will be considered as the answer. We now make sure that asking for
        # extra information like `description` or `inventory` before answering
        # the question works.
        assert game_state.description == previous_description
        assert game_state.inventory == previous_inventory

        # Now answering the question.
        game_state, _, _ = env.step("apple")
        assert "That's not a verb I recognise." not in game_state.feedback
        assert "tasty orange" not in game_state.inventory
        assert "tasty apple" in game_state.inventory
        assert "tasty apple" not in game_state.description


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
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file, EnvInfos(description=True, inventory=True))
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

    # Actions with two arguments.
    M = textworld.GameMaker()
    roomA = M.new_room("roomA")
    roomB = M.new_room("roomB")
    roomC = M.new_room("roomC")
    M.set_player(roomA)

    path = M.connect(roomA.east, roomB.west)
    gateway = M.new_door(path, name="gateway")

    path = M.connect(roomA.west, roomC.east)
    rectangular_gateway = M.new_door(path, name="rectangular gateway")

    keycard = M.new(type="k", name="keycard")
    rectangular_keycard = M.new(type="k", name="rectangular keycard")
    roomA.add(keycard, rectangular_keycard)

    M.add_fact("match", keycard, gateway)
    M.add_fact("match", rectangular_keycard, rectangular_gateway)
    M.add_fact("locked", gateway)
    M.add_fact("locked", rectangular_gateway)

    game = M.build()
    game_name = "test_names_disambiguation"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file, EnvInfos(description=True, inventory=True))
        env.reset()
        game_state, _, done = env.step("take keycard")
        assert "keycard" in game_state.inventory
        game_state, _, done = env.step("take keycard")  # Already in your inventory.
        assert "rectangular keycard" not in game_state.inventory
        game_state, _, done = env.step("take rectangular keycard")
        assert "rectangular keycard" in game_state.inventory

        game_state, _, done = env.step("unlock gateway with rectangular keycard")
        assert "That doesn't seem to fit the lock." in game_state.feedback
        game_state, _, done = env.step("unlock gateway with keycard")
        game_state, _, done = env.step("open gateway")
        game_state, _, done = env.step("go east")
        assert "-= Roomb =-" in game_state.description

        game_state, _, done = env.step("go west")
        game_state, _, done = env.step("unlock rectangular gateway with keycard")
        assert "That doesn't seem to fit the lock." in game_state.feedback
        game_state, _, done = env.step("unlock rectangular gateway with rectangular keycard")
        game_state, _, done = env.step("open rectangular gateway")
        game_state, _, done = env.step("go west")
        assert "-= Roomc =-" in game_state.description

    # Test invariance of the order in which ambiguous object names are defined.
    # First define "type G safe" then a "safe".
    M = textworld.GameMaker()
    garage = M.new_room("garage")
    M.set_player(garage)

    key = M.new(type="k", name="key")
    typeG_safe = M.new(type="c", name="type G safe")
    safe = M.new(type="c", name="safe")

    safe.add(key)
    garage.add(safe, typeG_safe)

    M.add_fact("open", safe)

    game = M.build()
    game_name = "test_names_disambiguation"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file, EnvInfos(inventory=True))
        game_state = env.reset()
        game_state, _, done = env.step("take key from safe")
        assert "key" in game_state.inventory

    # First define "safe" then "type G safe".
    M = textworld.GameMaker()
    garage = M.new_room("garage")
    M.set_player(garage)

    key = M.new(type="k", name="key")
    safe = M.new(type="c", name="safe")
    typeG_safe = M.new(type="c", name="type G safe")

    safe.add(key)
    garage.add(safe, typeG_safe)

    M.add_fact("open", safe)

    game = M.build()
    game_name = "test_names_disambiguation"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file, EnvInfos(inventory=True))
        game_state = env.reset()
        game_state, _, done = env.step("take key from safe")
        assert "key" in game_state.inventory


def test_take_all_and_variants():
    M = textworld.GameMaker()

    # Empty room.
    room = M.new_room("room")
    M.set_player(room)

    game = M.build()
    game_name = "test_take_all_and_variants"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
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
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file, EnvInfos(inventory=True))
        env.reset()

        game_state, _, done = env.step("take all ball")
        assert "red ball:" in game_state.feedback
        assert "blue ball:" in game_state.feedback
        assert "red ball" in game_state.inventory
        assert "blue ball" in game_state.inventory


def test_optional_and_repeatable_quests():
    M = textworld.GameMaker()
    museum = M.new_room("Museum")

    weak_statue = M.new(type="o", name="ivory statue")
    normal_statue = M.new(type="o", name="stone statue")
    strong_statue = M.new(type="o", name="granite statue")

    museum.add(weak_statue)
    museum.add(normal_statue)
    museum.add(strong_statue)

    M.set_player(museum)

    M.quests = [
        Quest(
            win_events=[
                Event(conditions=[M.new_fact('in', weak_statue, M.inventory)]),
            ],
            reward=-10,
            optional=True,
            repeatable=True
        ),
        Quest(
            win_events=[
                Event(conditions=[M.new_fact('in', normal_statue, M.inventory)]),
            ],
            reward=3,
            optional=True
        ),
        Quest(
            win_events=[
                Event(conditions=[M.new_fact('in', strong_statue, M.inventory)]),
            ],
            reward=5,
        )
    ]
    M.set_walkthrough(["take ivory", "take stone", "drop ivory", "take granite"])

    game = M.build()
    game_name = "test_optional_and_repeatable_quests"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file)
        state = env.reset()
        state.max_score == 8  # 5 (main quest) + 3 (optional quest)

        state, score, done = env.step("take ivory")
        assert not done
        assert score == -10

        state, score, done = env.step("look")
        assert score == -20

        state, score, done = env.step("take stone")
        assert not done
        assert score == -27  # -10 + 3

        state, score, done = env.step("drop ivory")
        assert score == -27

        state, score, done = env.step("take granite")
        assert done
        assert score == -22  # +5.
        assert "-22 out of a possible 8" in state.feedback


def test_game_with_infinite_max_score():
    M = textworld.GameMaker()
    museum = M.new_room("Museum")

    statue = M.new(type="o", name="golden statue")
    pedestal = M.new(type="s", name="pedestal")

    pedestal.add(statue)
    museum.add(pedestal)

    M.set_player(museum)

    M.quests = [
        Quest(
            win_events=[
                Event(conditions=[M.new_fact('in', statue, M.inventory)]),
            ],
            reward=10,
            optional=True,
            repeatable=True
        ),
        Quest(
            win_events=[
                Event(conditions=[M.new_fact('at', statue, museum)]),
            ],
            reward=0
        )
    ]
    M.set_walkthrough(["take statue from pedestal", "look", "drop statue"])

    game = M.build()
    game_name = "test_game_with_infinite_max_score"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = _compile_game(game, path=tmpdir)
        env = textworld.start(game_file)
        state = env.reset()
        state.max_score == np.inf  # Score increases for each turn the player hold the statue.

        state, score, done = env.step("look")
        assert not done
        assert score == 0

        state, score, done = env.step("take statue")
        assert score == 10

        state, score, done = env.step("wait")
        assert score == 20

        state, score, done = env.step("score")
        assert score == 20
        assert "You have so far scored 20 points," in state.feedback

        state, score, done = env.step("wait")
        assert score == 30

        state, score, done = env.step("drop statue")
        assert done
        assert score == 30

        assert "a total of 30 points," in state.feedback
