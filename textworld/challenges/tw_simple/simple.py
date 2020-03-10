"""
.. _simple_game:

A Simple Game
=============

This simple game takes place in a typical house and consists in
finding the right food item and cooking it.

Here's the map of the house.

::

                Bathroom
                    +
                    |
                    +
    Bedroom +--+ Kitchen +----+ Backyard
                    +              +
                    |              |
                    +              +
               Living Room       Garden

"""

import os
import argparse
from os.path import join as pjoin
from typing import Mapping, Optional

import textworld
from textworld.challenges import register

from textworld import GameOptions
from textworld.generator.data import KnowledgeBase
from textworld.generator.game import Quest, Event

from textworld.utils import encode_seeds


KB_PATH = pjoin(os.path.dirname(__file__), "textworld_data")


def build_argparser(parser=None):
    parser = parser or argparse.ArgumentParser()

    group = parser.add_argument_group('Simple game settings')
    group.add_argument("--rewards", required=True, choices=["dense", "balanced", "sparse"],
                       help="The reward frequency: dense, balanced, or sparse.")
    group.add_argument('--goal', required=True, choices=["detailed", "brief", "none"],
                       help="The description of the game's objective shown at the beginning of the game:"
                            " detailed, bried, or none")
    group.add_argument('--test', action="store_true",
                       help="Whether this game should be drawn from the test distributions of games.")

    return parser


def make(settings: Mapping[str, str], options: Optional[GameOptions] = None) -> textworld.Game:
    """ Make a simple game.

    Arguments:
        settings: Difficulty settings (see notes).
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.

    Notes:
        The settings that can be provided are:

        * rewards : The reward frequency: dense, balanced, or sparse.
        * goal : The description of the game's objective shown at the
          beginning of the game: detailed, bried, or none.
        * test : Whether this game should be drawn from the test
          distributions of games.
    """
    # Load knowledge base specific to this challenge.
    options.kb = KnowledgeBase.load(KB_PATH)

    metadata = {}  # Collect infos for reproducibility.
    metadata["desc"] = "Simple game"
    metadata["seeds"] = options.seeds
    metadata["world_size"] = 6
    metadata["quest_length"] = None  # TBD

    rngs = options.rngs
    rng_quest = rngs['quest']

    # Make the generation process reproducible.
    textworld.g_rng.set_seed(2018)

    M = textworld.GameMaker(options)

    # Start by building the layout of the world.
    bedroom = M.new_room("bedroom")
    kitchen = M.new_room("kitchen")
    livingroom = M.new_room("living room")
    bathroom = M.new_room("bathroom")
    backyard = M.new_room("backyard")
    garden = M.new_room("garden")

    # Connect rooms together.
    bedroom_kitchen = M.connect(bedroom.east, kitchen.west)
    M.connect(kitchen.north, bathroom.south)
    M.connect(kitchen.south, livingroom.north)
    kitchen_backyard = M.connect(kitchen.east, backyard.west)
    M.connect(backyard.south, garden.north)

    # Add doors.
    bedroom_kitchen.door = M.new(type='d', name='wooden door')
    kitchen_backyard.door = M.new(type='d', name='screen door')

    kitchen_backyard.door.add_property("closed")

    # Design the bedroom.
    drawer = M.new(type='c', name='chest drawer')
    trunk = M.new(type='c', name='antique trunk')
    bed = M.new(type='s', name='king-size bed')
    bedroom.add(drawer, trunk, bed)

    # Close the trunk and drawer.
    trunk.add_property("closed")
    drawer.add_property("closed")

    # - The bedroom's door is locked
    bedroom_kitchen.door.add_property("locked")

    # Design the kitchen.
    counter = M.new(type='s', name='counter')
    stove = M.new(type='s', name='stove')
    kitchen_island = M.new(type='s', name='kitchen island')
    refrigerator = M.new(type='c', name='refrigerator')
    kitchen.add(counter, stove, kitchen_island, refrigerator)

    # - Add some food in the refrigerator.
    apple = M.new(type='f', name='apple')
    milk = M.new(type='f', name='milk')
    refrigerator.add(apple, milk)

    # Design the bathroom.
    toilet = M.new(type='c', name='toilet')
    sink = M.new(type='s', name='sink')
    bath = M.new(type='c', name='bath')
    bathroom.add(toilet, sink, bath)

    toothbrush = M.new(type='o', name='toothbrush')
    sink.add(toothbrush)
    soap_bar = M.new(type='o', name='soap bar')
    bath.add(soap_bar)

    # Design the living room.
    couch = M.new(type='s', name='couch')
    low_table = M.new(type='s', name='low table')
    tv = M.new(type='s', name='tv')
    livingroom.add(couch, low_table, tv)

    remote = M.new(type='o', name='remote')
    low_table.add(remote)
    bag_of_chips = M.new(type='f', name='half of a bag of chips')
    couch.add(bag_of_chips)

    # Design backyard.
    bbq = M.new(type='s', name='bbq')
    patio_table = M.new(type='s', name='patio table')
    chairs = M.new(type='s', name='set of chairs')
    backyard.add(bbq, patio_table, chairs)

    # Design garden.
    shovel = M.new(type='o', name='shovel')
    tomato = M.new(type='f', name='tomato plant')
    pepper = M.new(type='f', name='bell pepper')
    lettuce = M.new(type='f', name='lettuce')
    garden.add(shovel, tomato, pepper, lettuce)

    # Close all containers
    for container in M.findall(type='c'):
        container.add_property("closed")

    # Set uncooked property for to all food items.
    foods = M.findall(type='f')
    for food in foods:
        food.add_property("edible")

    food_names = [food.name for food in foods]

    # Shuffle the position of the food items.
    rng_quest.shuffle(food_names)

    for food, name in zip(foods, food_names):
        food.orig_name = food.name
        food.infos.name = name

    # The player starts in the bedroom.
    M.set_player(bedroom)

    # Quest
    walkthrough = []

    # Part I - Escaping the room.
    # Generate the key that unlocks the bedroom door.
    bedroom_key = M.new(type='k', name='old key')
    M.add_fact("match", bedroom_key, bedroom_kitchen.door)

    # Decide where to hide the key.
    if rng_quest.rand() > 0.5:
        drawer.add(bedroom_key)
        walkthrough.append("open chest drawer")
        walkthrough.append("take old key from chest drawer")
        bedroom_key_holder = drawer
    else:
        trunk.add(bedroom_key)
        walkthrough.append("open antique trunk")
        walkthrough.append("take old key from antique trunk")
        bedroom_key_holder = trunk

    # Unlock the door, open it and leave the room.
    walkthrough.append("unlock wooden door with old key")
    walkthrough.append("open wooden door")
    walkthrough.append("go east")

    # Part II - Find food item.
    # 1. Randomly pick a food item to cook.
    food = rng_quest.choice(foods)

    if settings["test"]:
        TEST_FOODS = ["garlic", "kiwi", "carrot"]
        food.infos.name = rng_quest.choice(TEST_FOODS)

    # Retrieve the food item and get back in the kitchen.
    # HACK: handcrafting the walkthrough.
    if food.orig_name in ["apple", "milk"]:
        rooms_to_visit = []
        doors_to_open = []
        walkthrough.append("open refrigerator")
        walkthrough.append("take {} from refrigerator".format(food.name))
    elif food.orig_name == "half of a bag of chips":
        rooms_to_visit = [livingroom]
        doors_to_open = []
        walkthrough.append("go south")
        walkthrough.append("take {} from couch".format(food.name))
        walkthrough.append("go north")
    elif food.orig_name in ["bell pepper", "lettuce", "tomato plant"]:
        rooms_to_visit = [backyard, garden]
        doors_to_open = [kitchen_backyard.door]
        walkthrough.append("open screen door")
        walkthrough.append("go east")
        walkthrough.append("go south")
        walkthrough.append("take {}".format(food.name))
        walkthrough.append("go north")
        walkthrough.append("go west")

    # Part II - Cooking the food item.
    walkthrough.append("put {} on stove".format(food.name))
    # walkthrough.append("cook {}".format(food.name))
    # walkthrough.append("eat {}".format(food.name))

    # 2. Determine the winning condition(s) of the subgoals.
    quests = []
    bedroom_key_holder

    if settings["rewards"] == "dense":
        # Finding the bedroom key and opening the bedroom door.
        # 1. Opening the container.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("open", bedroom_key_holder)})
            ])
        )

        # 2. Getting the key.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("in", bedroom_key, M.inventory)})
            ])
        )

        # 3. Unlocking the bedroom door.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("closed", bedroom_kitchen.door)})
            ])
        )

        # 4. Opening the bedroom door.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("open", bedroom_kitchen.door)})
            ])
        )

    if settings["rewards"] in ["dense", "balanced"]:
        # Escaping out of the bedroom.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("at", M.player, kitchen)})
            ])
        )

    if settings["rewards"] in ["dense", "balanced"]:
        # Opening doors.
        for door in doors_to_open:
            quests.append(
                Quest(win_events=[
                    Event(conditions={M.new_fact("open", door)})
                ])
            )

    if settings["rewards"] == "dense":
        # Moving through places.
        for room in rooms_to_visit:
            quests.append(
                Quest(win_events=[
                    Event(conditions={M.new_fact("at", M.player, room)})
                ])
            )

    if settings["rewards"] in ["dense", "balanced"]:
        # Retrieving the food item.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("in", food, M.inventory)})
            ])
        )

    if settings["rewards"] in ["dense", "balanced", "sparse"]:
        # Putting the food on the stove.
        quests.append(
            Quest(win_events=[
                Event(conditions={M.new_fact("on", food, stove)})
            ])
        )

    # 3. Determine the losing condition(s) of the game.
    quests.append(
        Quest(fail_events=[
            Event(conditions={M.new_fact("eaten", food)})
        ])
    )

    # Set the subquest(s).
    M.quests = quests

    # - Add a hint of what needs to be done in this game.
    objective = "The dinner is almost ready! It's only missing a grilled {}."
    objective = objective.format(food.name)
    note = M.new(type='o', name='note', desc=objective)
    kitchen_island.add(note)

    M.set_walkthrough(walkthrough)
    game = M.build()

    if settings["goal"] == "detailed":
        # Use the detailed version of the objective.
        pass
    elif settings["goal"] == "brief":
        # Use a very high-level description of the objective.
        game.objective = objective
    elif settings["goal"] == "none":
        # No description of the objective.
        game.objective = ""

    game.metadata.update(metadata)
    uuid = "tw-simple-r{rewards}+g{goal}+{dataset}-{flags}-{seeds}"
    uuid = uuid.format(rewards=str.title(settings["rewards"]), goal=str.title(settings["goal"]),
                       dataset="test" if settings["test"] else "train",
                       flags=options.grammar.uuid,
                       seeds=encode_seeds([options.seeds[k] for k in sorted(options.seeds)]))
    game.metadata["uuid"] = uuid
    game.metadata["walkthrough"] = walkthrough
    return game


# Register this simple game.
register(name="tw-simple",
         desc="Generate simple challenge game",
         make=make,
         add_arguments=build_argparser)
