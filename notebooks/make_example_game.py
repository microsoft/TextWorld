# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import argparse

import textworld
from textworld import g_rng
from textworld import GameMaker
from textworld.logic import Proposition


def make_example_game(args):
    """
    This game takes place in a typical house and consists in
    three puzzles:
    1) Escape the room;
    2) Find the missing ingredient;
    3) Finish preparing the dinner.

    Here's the map of the house.
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
    # Make the generation process reproducible.
    g_rng.set_seed(2018)

    M = GameMaker()
    # Start by building the layout of the world.
    bedroom = M.new_room("bedroom")
    kitchen = M.new_room("kitchen")
    livingroom = M.new_room("living room")
    bathroom = M.new_room("bathroom")
    backyard = M.new_room("backyard")
    garden = M.new_room("garden")

    # Connect rooms together.
    bedroom_kitchen = M.connect(bedroom.east, kitchen.west)
    kitchen_bathroom = M.connect(kitchen.north, bathroom.south)
    kitchen_livingroom = M.connect(kitchen.south, livingroom.north)
    kitchen_backyard = M.connect(kitchen.east, backyard.west)
    backyard_garden = M.connect(backyard.south, garden.north)

    # Add doors.
    bedroom_kitchen.door = M.new(type='d', name='wooden door')
    kitchen_backyard.door = M.new(type='d', name='screen door')

    kitchen_backyard.door.add_property("closed")

    # Design the bedroom.
    drawer = M.new(type='c', name='chest drawer')
    trunk = M.new(type='c', name='antique trunk')
    bed = M.new(type='s', name='king-size bed')
    bedroom.add(drawer, trunk, bed)

    # - The bedroom's door is locked
    bedroom_kitchen.door.add_property("locked")

    # - and the key is in the drawer.
    bedroom_key = M.new(type='k', name='old key')
    drawer.add(bedroom_key)
    drawer.add_property("closed")
    M.add_fact("match", bedroom_key, bedroom_kitchen.door)

    # - Describe the room.
    bedroom.desc = ""

    # Design the kitchen.
    counter = M.new(type='s', name='counter')
    stove = M.new(type='s', name='stove')
    kitchen_island = M.new(type='s', name='kitchen island')
    refrigerator = M.new(type='c', name='refrigerator')
    kitchen.add(counter, stove, kitchen_island, refrigerator)

    # - Add note on the kitchen island.
    objective = "The dinner is almost ready! It's only missing a grilled carrot."
    note = M.new(type='o', name='note',
                 desc=objective)
    kitchen_island.add(note)

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
    carrot = M.new(type='f', name='carrot')
    lettuce = M.new(type='f', name='lettuce')
    garden.add(shovel, tomato, carrot, lettuce)

    # Close all containers
    for container in M.findall(type='c'):
        container.add_property("closed")

    # Set uncooked property for to all food items.
    # NOT IMPLEMENTED YET
    # for food in M.findall(type='f'):
    #     food.add_property("edible")
    #     food.add_property("raw")

    # The player starts in the bedroom.
    M.set_player(bedroom)

    # To define a quest we are going to record it by playing the game.
    # print("******* Recording a quest. Hit 'Ctrl + C' when done. *******")
    # M.record_quest()
    commands = [
        "open chest drawer",
        "take old key from chest drawer",
        "unlock wooden door with old key",
        "open wooden door",
        "go east"
    ]

    if args.type in ["short", "medium", "long", "last", "human"]:
        commands.append("open screen door")

    if args.type in ["medium", "long", "last", "human"]:
        commands.extend([
            "go east",
            "go south",
            "take carrot"
        ])

    if args.type in ["long", "last", "human"]:
        commands.extend([
            "go north",
            "go west",
            "put carrot on stove",
            # "cook carrot"  # Not supported yet.
        ])

    quest = M.set_quest_from_commands(commands)

    # TODO: Provide better API to specify failing conditions.
    quest.set_failing_conditions([Proposition("eaten", [carrot.var])])

    if args.type == "human":
        # Use a very high-level description of the objective.
        quest.desc = ""

    elif args.type == "last":
        # Use a very high-level description of the objective.
        quest.desc = objective

    print(quest.desc)

    game_file = M.compile(args.filename)
    print("*** Game created: {}".format(game_file))
    return game_file


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="example",
                        help="Name of the generated game. Default: example.")
    parser.add_argument("--type", choices=["baby", "short", "medium", "long", "last", "human"],
                        help="Select which test game to generate: baby, short, medium, long or human. Default: long.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    game_file = make_example_game(args)
