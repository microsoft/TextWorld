import argparse
import os

from os.path import join as pjoin
from typing import Mapping, Optional

import textworld

from textworld import g_rng
from textworld import GameMaker
from textworld.challenges import register
from textworld.generator.data import KnowledgeBase
from textworld.generator.game import GameOptions, Event, Quest, GameProgression


g_rng.set_seed(20190826)
PATH = os.path.dirname(__file__)


def build_argparser(parser=None):
    parser = parser or argparse.ArgumentParser()

    group = parser.add_argument_group('Spaceship game settings')
    group.add_argument("--level", required=True, choices=["easy", "medium", "difficult"],
                       help="The difficulty level. Must be between: easy, medium, or difficult.")
    general_group = argparse.ArgumentParser(add_help=False)
    general_group.add_argument("--third-party", metavar="PATH",
                               help="Load third-party module. Useful to register new custom challenges on-the-fly.")
    return parser


def make_game_medium(settings: Mapping[str, str], options: Optional[GameOptions] = None) -> textworld.Game:
    """ Make a Spaceship game of the desired difficulty settings.

    Arguments:
        settings: Difficulty settings (see notes).
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.

    Notes:
        Difficulty levels are defined as follows:
        * Level easy.
        * Level medium.
        * Level difficult.

    """
    kb = KnowledgeBase.load(target_dir=pjoin(os.path.dirname(__file__), 'textworld_data'))
    options = options or GameOptions()
    options.grammar.theme = 'spaceship'
    options.kb = kb
    options.seeds = g_rng.seed

    rngs = options.rngs
    rng_map = rngs['map']
    rng_objects = rngs['objects']
    rng_grammar = rngs['grammar']
    rng_quest = rngs['quest']

    if settings["level"] == 'easy':
        mode = "easy"
        options.nb_rooms = 4

    elif settings["level"] == 'medium':
        mode = "medium"
        options.nb_rooms = 8

    elif settings["level"] == 'difficult':
        mode = "difficult"
        options.nb_rooms = 8

    metadata = {"desc": "Spaceship",  # Collect information for reproduction.
                "mode": mode,
                "seeds": options.seeds,
                "world_size": options.nb_rooms}

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #                                    Create the Game Environment
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    gm = GameMaker(options=options)
    # gm = GameMaker(kb=kb, theme='spaceship')

    # ===== Sleep Station Design =======================================================================================
    sleep_station = gm.new_room("Sleep Station")
    sleep_station.infos.desc = "This is a typical bedroom in spaceship; here,  it is called sleep station. It is " \
                               "small but comfortable to take a good rest after a day full of missions. However, " \
                               "today your mission will start from here. Wait to be notified by a message. So, you " \
                               "should find that message first." \
                               " " \
                               "BTW, don't forget that when the Hatch door is open, you should already have worn " \
                               "your specially-designed outfit to be able to enter and stay at Hatch area; otherwise " \
                               "you'll die! Yes! Living in space is tough."

    surf_0 = gm.new(type='s', name='vertical desk')  # surf_0 is a table (supporter) in the Sleep Station.
    surf_0.infos.desc = "This is not a regular table. The surface is installed vertically and your objects are " \
                        "attached or hooked to it, why? Come on! we are in space, there is no gravity here."
    sleep_station.add(surf_0)

    laptop = gm.new(type='cpu', name='laptop')
    laptop.infos.desc = "This is your personal laptop which is attached to the surface of the table. You can do " \
                        "regular things with this, like check your emails, watch YouTube, Skype with family,etc." \
                        "Since you are here, we recommend you to check your emails. New missions are posted through " \
                        "emails."
    surf_0.add(laptop)
    gm.add_fact('unread/e', laptop)

    # ===== US LAB Design ==============================================================================================
    us_lab = gm.new_room("US LAB")
    us_lab.infos.desc = "This is where Americans do their research on Space. In addition to all computers and " \
                        "lab gadgets, you can find a couple of objects here which are useful during your mission. " \
                        "Let's explore the room."

    box_a = gm.new(type='c', name="box A")
    box_a.infos.desc = "This a regular box, keeps the electronic key to open box B. "
    us_lab.add(box_a)
    gm.add_fact("closed", box_a)

    key_0 = gm.new(type='k', name="electronic key")
    key_0.infos.desc = "This key is an electronic key which unlocks box B. An electronic key is in fact a code and " \
                       "opens those locks which are equipped with a keypad."
    box_a.add(key_0)

    corridor_1 = gm.connect(sleep_station.south, us_lab.north)
    door_a = gm.new_door(corridor_1, name="door A")
    gm.add_fact("closed", door_a)

    # ===== Russian Module Design ======================================================================================
    russian_module = gm.new_room("Russian Module")
    russian_module.infos.desc = "The Russian module is a typical space lab that you can expect, filled with a " \
                                "lot of processing machines, test equipments and space drive cars, in fact for " \
                                "repair and test. Since it is located at the center of International Space Station, " \
                                "it is also important room for everyone. There are many other objects here and " \
                                "there belongs to other astronauts, probably that's why here looks a bit messy. " \
                                "There are some stuffs here you should pick, obviously if you can find them among " \
                                "all this mess."

    surf_1 = gm.new(type='s', name='metal table')
    surf_1.infos.desc = "This is a big metal table, a messy one, there are many things on it, it is difficult to " \
                        "find what you want. However, there is just one item which is important for you. Try to " \
                        "find that item."
    russian_module.add(surf_1)

    box_b = gm.new(type='c', name="box B")
    box_b.infos.desc = "This box is locked! sounds it carries important item... So, let's find its key to open it. " \
                       "Wait... strange! the lock looks like a keypad!! Wait we've seen something similar to this " \
                       "somewhere before."
    surf_1.add(box_b)
    gm.add_fact("locked", box_b)
    gm.add_fact("match", key_0, box_b)

    push_button = gm.new(type='b', name="exit push button")
    push_button.infos.desc = "This push button is a key-like object which opens door C."
    gm.add_fact("unpushed", push_button)
    box_b.add(push_button)

    corridor_2 = gm.connect(us_lab.south, russian_module.north)
    door_b = gm.new_door(corridor_2, name="door B")
    gm.add_fact("closed", door_b)

    # ===== Hatch Design ===============================================================================================
    hatch = gm.new_room("Hatch")
    hatch.infos.desc = "This area is like the entrance to the spaceship, so like home entrance with outer and " \
                       "inner doors and a place that outfits are hooked. There are only two important differences: " \
                       "first, if the outer door is open and you don't have outfit on you, you are dead!! No joke " \
                       "here! So make sure that you open the door after wearing those cloths. Second, the door nob " \
                       "to open the door is not neither on the door nor in this room. You should open the external " \
                       "door from Russian Module! woooh so much of safety concerns, yeah?!"

    cloth = gm.new(type='l', name="outfit")
    hatch.add(cloth)
    gm.add_fact("takenoff", cloth)
    gm.add_fact("clean", cloth)

    corridor_3 = gm.connect(hatch.west, russian_module.east)
    door_c = gm.new_door(corridor_3, name="door C")
    gm.add_fact("closed", door_c)

    # ===== Outside Spaceship (Space) Design ===========================================================================
    outside = gm.new_room("Outside")
    outside.infos.desc = "Here is outside the spaceship. No Oxygen, no gravity, nothing! If you are here, it means " \
                         "that you have the special outfit on you and you passed the medium level of the game " \
                         "successfully! Congrats!"

    corridor_4 = gm.connect(outside.north, hatch.south)
    door_d = gm.new_door(corridor_4, name="door D")
    gm.add_fact("locked", door_d)
    gm.add_fact("pair", push_button, door_d)

    # ===== Player and Inventory Design ================================================================================
    gm.set_player(sleep_station)

    game = quest_design_medium(gm)

    # from textworld.challenges.spaceship import maker
    # maker.test_commands(gm, [
    #     'check laptop for email',
    #     'check laptop for email',
    #     'open door A',
    #     'go south',
    #     'open box A',
    #     'take electronic key from box A',
    #     'open door B',
    #     'go south',
    #
    #     'unlock box B with electronic key',
    #     'open box B',
    #     'push exit push button',
    #
    #     'open door C',
    #     'go east',
    #     'take outfit',
    #     'wear outfit',
    #     'go west',
    #     'go east',
    #     'go south',
    #
    #     # 'check laptop for email',
    #     # 'check laptop for email',
    #     # 'open door A',
    #     # 'go south',
    #     # 'open box A',
    #     # 'take electronic key from box A',
    #     # 'open door B',
    #     # 'go south',
    #     # 'open door C',
    #     # 'go east',
    #     # 'take outfit',
    #     # 'wear outfit',
    #     # 'go west',
    #     # 'unlock box B with electronic key',
    #     # 'open box B',
    #     # 'push exit push button',
    #     # 'go east',
    #     # 'go south',
    # ])

    game.metadata = metadata
    uuid = "tw-spaceship-{level}".format(level=str.title(settings["level"]))
    game.metadata["uuid"] = uuid

    return game


def make_game_difficult(settings: Mapping[str, str], options: Optional[GameOptions] = None) -> textworld.Game:
    """ Make a Spaceship game of the desired difficulty settings.

    Arguments:
        settings: Difficulty settings (see notes).
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.

    Notes:
        Difficulty levels are defined as follows:
        * Level easy.
        * Level medium.
        * Level difficult.

    """
    kb = KnowledgeBase.load(target_dir=pjoin(os.path.dirname(__file__), 'textworld_data'))
    options = options or GameOptions()
    options.grammar.theme = 'spaceship'
    options.kb = kb
    options.seeds = g_rng.seed

    rngs = options.rngs
    rng_map = rngs['map']
    rng_objects = rngs['objects']
    rng_grammar = rngs['grammar']
    rng_quest = rngs['quest']

    if settings["level"] == 'easy':
        mode = "easy"
        options.nb_rooms = 4

    elif settings["level"] == 'medium':
        mode = "medium"
        options.nb_rooms = 8

    elif settings["level"] == 'difficult':
        mode = "difficult"
        options.nb_rooms = 8

    metadata = {"desc": "Spaceship",  # Collect information for reproduction.
                "mode": mode,
                "seeds": options.seeds,
                "world_size": options.nb_rooms}

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #                                    Create the Game Environment
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    gm = GameMaker(kb=kb, theme='spaceship')

    # ===== Sleep Station Design =======================================================================================
    sleep_station = gm.new_room("Sleep Station")
    sleep_station.infos.desc = "This is a typical bedroom in spaceship; here,  it is called sleep station. It is " \
                               "small but comfortable to take a good rest after a day full of missions. However, " \
                               "today your mission will start from here. Wait to be notified by a message. So, you " \
                               "should find that message first." \
                               " " \
                               "BTW, don't forget that when the Hatch door is open, you should already have worn " \
                               "your specially-designed outfit to be able to enter and stay at Hatch area; otherwise " \
                               "you'll die! Yes! Living in space is tough."

    sleep_bag = gm.new(type='c', name="sleeping bag")
    sleep_bag.infos.desc = "cool! You can sleep in a comfy bag."
    sleep_station.add(sleep_bag)  # Sleeping bag is fixed in place in the Sleep Station.
    gm.add_fact("open", sleep_bag)

    surf_1 = gm.new(type='s', name='vertical desk')  # surf_1 is a table (supporter) in the Sleep Station.
    surf_1.infos.desc = "This is not a regular table. The surface is installed vertically and your objects are " \
                        "attached or hooked to it, why? Come on! we are in space, there is no gravity here."
    sleep_station.add(surf_1)  # The card box contains nothing at this game

    laptop = gm.new(type='cpu', name='laptop')
    laptop.infos.desc = "This is your personal laptop which is attached to the surface of the table. You can do " \
                        "regular things with this, like check your emails, watch YouTube, Skype with family,etc." \
                        "Since you are here, we recommend you to check your emails. New missions are posted through " \
                        "emails."
    surf_1.add(laptop)
    gm.add_fact('unread/e', laptop)

    # ===== US LAB Design ==============================================================================================
    us_lab = gm.new_room("US LAB")
    us_lab.infos.desc = "This is where Americans do their research on Space. In addition to all computers and " \
                        "lab gadgets, you can find a couple of objects here which are useful during our game. Let's " \
                        "explore the room."

    box_a = gm.new(type='c', name="box A")
    box_a.infos.desc = "This a regular box, keeps the electronic key to open door C. But it is locked. The lock " \
                       "looks like a keypad, means that the key is in fact just a code! So, ... let's search around " \
                       "to find its key."
    us_lab.add(box_a)
    gm.add_fact("locked", box_a)

    key_1 = gm.new(type='k', name="electronic key 1")
    key_1.infos.desc = "This key is a card key which opens door C."
    box_a.add(key_1)

    corridor_1 = gm.connect(sleep_station.south, us_lab.north)
    door_a = gm.new_door(corridor_1, name="door A")
    gm.add_fact("closed", door_a)

    # ===== European Module Design =====================================================================================
    european_module = gm.new_room("European Module")
    european_module.infos.desc = "This room belongs to European scientists. Isn't it cool? what do they research? " \
                                 "well, we can explore it later... For now, there is a key code here. This code " \
                                 "opens the box in the next room and consequently takes you to the next stage. So, " \
                                 "explore the table to find the key."

    surf_2 = gm.new(type='s', name='table')
    surf_2.infos.desc = "This is a simple table located in the middle of the room. Let's take a look at it..."
    european_module.add(surf_2)

    box_b = gm.new(type='c', name="box B")
    box_b.infos.desc = "This a regular box, keeps the key to open box A."
    surf_2.add(box_b)
    gm.add_fact("closed", box_b)

    key_2 = gm.new(type='k', name="code key 1")
    key_2.infos.desc = "This key is in fact a digital code which opens the box in the US Lab area. The code, " \
                       "in fact, is written on a piece of paper."
    box_b.add(key_2)
    gm.add_fact("match", key_2, box_a)

    chair_1 = gm.new(type='s', name='chair')
    chair_1.infos.desc = "this is a dark-gray chair which is developed to be used in space."
    european_module.add(chair_1)

    corridor2 = gm.connect(us_lab.east, european_module.west)

    # ===== Russian Module Design ======================================================================================
    russian_module = gm.new_room("Russian Module")
    russian_module.infos.desc = "The Russian module is a typical space lab that you can expect, filled with a " \
                                "lot of processing machines, test equipments and space drive cars, in fact for " \
                                "repair and test. Since it is located at the center of International Space Station, " \
                                "it is also important room for everyone. There are many other objects here and " \
                                "there belongs to other astronauts, probably that's why here looks a bit messy. " \
                                "There are some stuffs here you should pick, obviously if you can find them among " \
                                "all this mess."

    surf_3 = gm.new(type='s', name='metal table')
    surf_3.infos.desc = "This is a big metal table, a messy one, there are many things on it, it is difficult to " \
                        "find what you want. However, there is just one item which is important for you. Try to " \
                        "find that item."
    russian_module.add(surf_3)

    papers = gm.new(type='o', name='bunch of sticked papers')
    surf_3.add(papers)

    notebooks = gm.new(type='o', name='lots of hanged notebooks')
    surf_3.add(notebooks)

    tools = gm.new(type='o', name='attached bags for mechanical tools')
    surf_3.add(tools)

    box_c = gm.new(type='c', name="box C")
    box_c.infos.desc = "This box is locked! sounds it carries important item... So, let's find its key to open it. " \
                       "Wait... strange! the lock looks like a heart!! Wait we've seen something similar to this " \
                       "somewhere before."
    surf_3.add(box_c)
    gm.add_fact("locked", box_c)

    key_3 = gm.new(type='k', name="digital key 1")
    key_3.infos.desc = "This key is an important key in this craft. If you want to leave the spaceship, you " \
                       "definitely need this key."
    box_c.add(key_3)

    surf_4 = gm.new(type='s', name='wall-mounted surface')
    surf_4.infos.desc = "This is a wall-mounted surface which different instruments are installed on this. These " \
                        "instruments are basically control various modules and doors in the shuttle."
    russian_module.add(surf_4)

    box_d = gm.new(type='c', name="exit box")
    box_d.infos.desc = "The most important box here, which is in fact locked! sounds it carries important item... " \
                       "So, let's find its key to open it."
    surf_4.add(box_d)
    gm.add_fact("locked", box_d)

    push_button = gm.new(type='b', name="exit push button")
    push_button.infos.desc = "This push button is a key-like object which opens door A."
    gm.add_fact("unpushed", push_button)
    box_d.add(push_button)

    corridor3 = gm.connect(us_lab.south, russian_module.north)
    door_b = gm.new_door(corridor3, name="door B")
    gm.add_fact("match", key_1, door_b)  # Tell the game 'Electronic key' is matching the 'door B''s lock
    if settings["level"] == 'difficult':
        gm.add_fact("closed", door_b)
    else:
        gm.add_fact("locked", door_b)

    # ===== Lounge Design ==============================================================================================
    lounge = gm.new_room("Lounge Module")
    lounge.infos.desc = "This lounge is very quiet room with a big round window to the space. Wow, you can look " \
                        "to our beloved Earth from this window. This room is the place that you can stay here for " \
                        "hours and just get relax. This room also contains some other stuff, let's explore what " \
                        "they are ..."

    box_e = gm.new(type='c', name="box E")
    box_e.infos.desc = "This box is actually a wall-mounted bag and you can put an object into it. Since we have no " \
                       "gravity in the space, you can't just simply leave the object in the room. The object should " \
                       "be hooked or inserted into a container like this bag. Well, know we know what it is!"
    lounge.add(box_e)
    gm.add_fact("closed", box_e)

    key_4 = gm.new(type='k', name="electronic key 2")
    key_4.infos.desc = "This key is the key opens the door to the control room. Although it looks like a regular " \
                       "iron key, it is very special metal key! Not any other key can be like it. Make sure to keep " \
                       "it in safe place."
    box_e.add(key_4)

    corridor4 = gm.connect(russian_module.east, lounge.west)

    # ===== Control Module Design ======================================================================================
    control_module = gm.new_room("Control Module")
    control_module.infos.desc = "This is the heart of this spaceship! Wow ... look around, all the monitors and " \
                                "panels. It is like you can control everything from here; more interestingly, you " \
                                "can communicate with people on the Earth. There are also super important objects " \
                                "kept in this room. Let's find them."

    box_f = gm.new(type='c', name="secured box")
    box_f.infos.desc = "This box is secured very much, simple box with a complex, strange keypad to enter the code! " \
                       "So ... it should contain extremely important items in it. Isn't it the thing you are " \
                       "looking for?!"
    control_module.add(box_f)
    gm.add_fact("locked", box_f)
    gm.add_fact("match", key_3, box_f)

    book = gm.new(type='txt', name='Secret Codes Handbook')
    book.infos.desc = "If you open and check this book, here it is the description: 'This is a book of all secret " \
                      "codes to manage different actions and functions inside the International Space Station. " \
                      "These codes are pre-authorized by the main control room at Earth unless it is mentioned.'" \
                      " " \
                      "On the second page of the book, you can find this: 'To open the hatch door you should have " \
                      "both two keys in the secured box. ATTENTION: you MUST have the outfit on you, before opening " \
                      "the hatch. Otherwise, your life is in fatal danger.'"
    box_f.add(book)
    gm.add_fact("unread/t", book)

    key_5 = gm.new(type='k', name="digital key 2")
    box_f.add(key_5)
    gm.add_fact("match", key_5, box_d)

    key_6 = gm.new(type='k', name="code key 2")
    box_f.add(key_6)

    corridor5 = gm.connect(control_module.east, russian_module.west)
    door_c = gm.new_door(corridor5, name="door C")
    gm.add_fact("locked", door_c)
    gm.add_fact("match", key_4, door_c)  # Tell the game 'Electronic key' is matching the 'door B''s lock

    # ===== Hatch Design ===============================================================================================
    hatch = gm.new_room("Hatch")
    hatch.infos.desc = "This area is like the entrance to the spaceship, so like home entrance with outer and " \
                       "inner doors and a place that outfits are hooked. There are only two important differences: " \
                       "first, if the outer door is open and you don't have outfit on you, you are dead!! No joke " \
                       "here! So make sure that you open the door after wearing those cloths. Second, the door nob " \
                       "to open the door is not neither on the door nor in this room. You should open the external " \
                       "door from Russian Module! woooh so much of safety concerns, yeah?!"

    cloth = gm.new(type='l', name="outfit")
    hatch.add(cloth)
    gm.add_fact("takenoff", cloth)
    gm.add_fact("clean", cloth)

    corridor6 = gm.connect(hatch.north, lounge.south)
    door_d = gm.new_door(corridor6, name="door D")
    gm.add_fact("match", key_6, door_d)
    if settings["level"] == 'difficult':
        gm.add_fact("closed", door_d)
    else:
        gm.add_fact("locked", door_d)

    # ===== Outside Spaceship (Space) Design ===========================================================================
    outside = gm.new_room("Outside")
    outside.infos.desc = "Here is outside the spaceship. No Oxygen, no gravity, nothing! If you are here, it means " \
                         "that you have the special outfit on you and you passed the medium level of the game! " \
                         "Congrats!"

    corridor7 = gm.connect(outside.north, hatch.south)
    door_e = gm.new_door(corridor7, name="door E")
    gm.add_fact("locked", door_e)
    gm.add_fact("pair", push_button, door_e)

    # ===== Player and Inventory Design ================================================================================
    if settings["level"] == 'difficult':
        # Randomly place the player in a subset of rooms.
        # The player can be randomly start from any room but two of them: Control Module and Outside
        available_rooms = []
        for rum in gm.rooms:
            if (rum is not gm._named_entities['Outside']) and (rum is not gm._named_entities['Control Module']):
                available_rooms.append(rum)

        starting_room = None
        if len(available_rooms) > 1:
            starting_room = rng_map.choice(available_rooms)

        gm.set_player(starting_room)

    else:
        gm.set_player(sleep_station)

    # key_7 = gm.new(type='k', name="hearty key")
    # key_7.infos.desc = "This key is shaped like a heart, not a normal key for a spaceship, ha ha ha..."
    # gm.add_fact("match", key_7, box_c)
    # gm.inventory.add(key_7)  # Add the object to the player's inventory.

    if settings["level"] == 'easy':
        game = quest_design_easy(gm)

    elif settings["level"] == 'medium':
        game = quest_design_medium(gm)

    elif settings["level"] == 'difficult':
        game = quest_design_difficult(gm)

    # from textworld.challenges.spaceship import maker
    # maker.test_commands(gm, [
    #     'check laptop for email',
    #     # 'check laptop for email',
    #     'open door A',
    #     'go south',
    # ])

    game.metadata = metadata
    uuid = "tw-spaceship-{level}".format(level=str.title(settings["level"]))
    game.metadata["uuid"] = uuid

    return game


def quest_design_easy(game):
    return None


def quest_design_medium(game):
    quests = []

    # 1. Is the Player performing successful in the Sleeping Station
    win_quest = Event(conditions={
        game.new_fact("at", game._entities['P'], game._entities['r_0'])
    })
    quests.append(Quest(win_events=[win_quest], fail_events=[], reward=0))

    fail_quest = Event(conditions={
        game.new_fact("event", game._entities['P'], game._entities['r_0']),
        game.new_fact("at", game._entities['P'], game._entities['r_1']),
        game.new_fact("open", game._entities['d_0']),
        game.new_fact("unread/e", game._entities['cpu_0']),
    })

    win_quest = Event(conditions={
        game.new_fact("event", game._entities['P'], game._entities['r_0']),
        game.new_fact("at", game._entities['P'], game._entities['r_1']),
        game.new_fact("open", game._entities['d_0']),
        game.new_fact("read/e", game._entities['cpu_0']),
    })
    quests.append(Quest(win_events=[win_quest], fail_events=[fail_quest]))

    # 2. Player is in US LAB to find Electronic Key 1
    win_quest = Event(conditions={game.new_fact("in", game._entities['k_0'], game._entities['I'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))

    # 3. Player is in Russian Module and take digital Key 1 and/or push the button
    win_quest = Event(conditions={game.new_fact("pushed", game._entities['b_0']),
                                  game.new_fact("worn", game._entities['l_0'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))
    fail_quest = Event(conditions={game.new_fact("pushed", game._entities['b_0']),
                                   game.new_fact("takenoff", game._entities['l_0']),
                                   game.new_fact("open", game._entities['d_2'])})
    quests.append(Quest(win_events=[], fail_events=[fail_quest]))

    # 4. Player is in Hatch room and wears the cloth
    win_quest = Event(conditions={game.new_fact("worn", game._entities['l_0'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))

    # 5. Player goes outside
    win_quest = Event(conditions={game.new_fact("at", game._entities['P'], game._entities['r_4'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))

    game.quests = quests

    return game.build()


def quest_design_difficult(game):
    quests = []

    # 1. Is the Player performing successful in the Sleeping Station
    win_quest = Event(conditions={
        game.new_fact("at", game._entities['P'], game._entities['r_0'])
    })
    quests.append(Quest(win_events=[win_quest], fail_events=[], reward=0))

    fail_quest = Event(conditions={
        game.new_fact("event", game._entities['P'], game._entities['r_0']),
        game.new_fact("at", game._entities['P'], game._entities['r_1']),
        game.new_fact("open", game._entities['d_0']),
        game.new_fact("unread/e", game._entities['cpu_0']),
    })

    win_quest = Event(conditions={
        game.new_fact("event", game._entities['P'], game._entities['r_0']),
        game.new_fact("at", game._entities['P'], game._entities['r_1']),
        game.new_fact("open", game._entities['d_0']),
        game.new_fact("read/e", game._entities['cpu_0']),
    })
    quests.append(Quest(win_events=[win_quest], fail_events=[fail_quest]))

    # 2. Player is in US LAB to find Electronic Key 1
    win_quest = Event(conditions={game.new_fact("in", game._entities['k_0'], game._entities['I'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))

    # 3. Player is in Russian Module and take digital Key 1 and/or push the button
    win_quest = Event(conditions={game.new_fact("in", game._entities['k_2'], game._entities['I'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))
    win_quest = Event(conditions={game.new_fact("pushed", game._entities['b_0']),
                                  game.new_fact("worn", game._entities['l_0'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))
    fail_quest = Event(conditions={game.new_fact("pushed", game._entities['b_0']),
                                   game.new_fact("takenoff", game._entities['l_0'])})
    quests.append(Quest(win_events=[], fail_events=[fail_quest]))

    # # 4. Player is the Control Mo/dule and take Electronic Key 2
    # win_quest = Event(conditions={game.new_fact("in", game._entities['k_5'], game._entities['I'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    #
    # # 5. Player reads the Secret Code book at Control Module
    # win_quest = Event(conditions={game.new_fact("read/t", game._entities['txt_0'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    #
    # # 6. Player is in Hatch room and wears the cloth
    # win_quest = Event(conditions={game.new_fact("worn", game._entities['l_0'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    #
    # # 7. Player goes outside
    # win_quest = Event(conditions={game.new_fact("at", game._entities['P'], game._entities['r_7'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))

    game.quests = quests

    return game.build()


# g = make_game_medium({'level': 'medium'})


register(name="tw-spaceship",
         desc="Generate a Spaceship challenge game",
         make=make_game_medium,
         add_arguments=build_argparser)
