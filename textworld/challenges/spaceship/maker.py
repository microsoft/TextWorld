import os
from os.path import join as pjoin
from typing import Optional

from textworld import GameMaker
from textworld.generator.data import KnowledgeBase
from textworld import g_rng
from textworld.helpers import start
from textworld.utils import make_temp_directory
import textworld
from textworld.generator.game import EventCondition, Quest, GameOptions
from textworld.generator import World
from textworld.core import EnvInfos


g_rng.set_seed(20190826)
PATH = pjoin(os.path.dirname(__file__), 'textworld_data')


def spaceship_maker_level_easy():
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
    gm = GameMaker(kb=kb, theme='Spaceship')

    # ===== Sleep Station Design =======================================================================================
    sleep_station = gm.new_room("Sleep Station")

    sleep_bag = gm.new(type='c', name="sleeping bag")       # Provide the type and the name of the object.
    sleep_bag.infos.desc = "cool! You can sleep in a comfy bag."  # Text to display when issuing command "examine note".
    sleep_station.add(sleep_bag)  # Sleeping bag is fixed in place in the Sleep Station.
    gm.add_fact("open", sleep_bag)

    card_box = gm.new(type='c')   # Card box is a container which is fixed in place in the Sleep Station.
    card_box.infos.desc = "It is empty."
    sleep_station.add(card_box)   # The card box contains nothing at this game
    gm.add_fact("closed", card_box)

    # ===== US LAB Design ==============================================================================================
    us_lab = gm.new_room("US LAB")
    key = gm.new(type='k', name="electronic key")
    key.infos.desc = "This key opens the door into the modules area. In this space craft, the gravity is not a " \
                     "challenge. Thus, you can find things on the floor."
    us_lab.add(key)  # When added directly to a room, portable objects are put on the floor.

    corridor1 = gm.connect(sleep_station.south, us_lab.north)
    doorA = gm.new_door(corridor1, name="door A")
    gm.add_fact("closed", doorA)  # Add a fact about the door, e.g. here it is closed.

    # ===== Russian Module Design ======================================================================================
    russian_module = gm.new_room("Russian Module")
    supporter = gm.new(type='s')  # When not provided, names are automatically generated.
    russian_module.add(supporter)  # Supporters are fixed in place.
    key_code = gm.new(type='k', name="digital key")
    key_code.infos.desc = "This key is in fact a digital code which opens the secured box in the control modules " \
                          "area. The code, in fact, is written on the supporter."
    supporter.add(key_code)

    corridor2 = gm.connect(us_lab.south, russian_module.north)
    doorB = gm.new_door(corridor2, name="door B")
    gm.add_fact("locked", doorB)
    gm.add_fact("match", key, doorB)  # Tell the game 'Electronic key' is matching the 'door B''s lock

    # ===== Control Module Design ======================================================================================
    control_module = gm.new_room("Control Module")
    secured_box = gm.new(type='c', name='Secured box')  # When not provided, names are automatically generated.
    secured_box.infos.desc = "This box is highly secured with a complex code that is in one of the modules in the " \
                             "craft. To open the box, you should just find that code key."
    gm.add_fact("locked", secured_box)
    gm.add_fact("match", key_code, secured_box)
    secured_box.infos.desc = "The Secret Codes Handbook is in this box."
    control_module.add(secured_box)  # Supporters are fixed in place.
    book = gm.new(type='o', name='Secret Codes Handbook')  # New portable object with a randomly generated name.
    secured_box.add(book)

    corridor3 = gm.connect(russian_module.west, control_module.east)
    doorC = gm.new_door(corridor3, name='door C')
    gm.add_fact("open", doorC)

    # ===== Player and Inventory Design ================================================================================
    gm.set_player(sleep_station)

    pencil = gm.new(type='o', name='pencil')  # New portable object with a randomly generated name.
    gm.inventory.add(pencil)  # Add the object to the player's inventory.
    gm.render(interactive=True)

    quest = gm.new_quest_using_commands(['open door A', 'go south', 'take electronic key',
                                         'unlock door B with electronic key', 'open door B', 'go south',
                                         'take digital key from board', 'go west',
                                         'unlock Secured box with digital key', 'open Secured box',
                                         'take Secret Codes Handbook from Secured box'])
    print(" > ".join(quest.commands))

    gm.quests.append(quest)


def spaceship_maker_level_medium():
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
    gm = GameMaker(kb=kb, theme='Spaceship')

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
    sleep_station.add(surf_1)   # The card box contains nothing at this game

    # laptop = gm.new(type='o', name="laptop")
    laptop = gm.new(type='cpu', name='laptop')
    laptop.infos.desc = "This is your personal laptop which is attached to the surface of the table. You can do " \
                        "regular things with this, like check your emails, watch YouTube, Skype with family,etc." \
                        "Since you are here, we recommend you to check your emails. New missions are posted through " \
                        "emails. "
    surf_1.add(laptop)

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
    gm.add_fact("locked", door_b)
    gm.add_fact("match", key_1, door_b)  # Tell the game 'Electronic key' is matching the 'door B''s lock

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

    book = gm.new(type='o', name='Secret Codes Handbook')
    book.infos.desc = "If you open and check this book, here it is the description: 'This is a book of all secret " \
                      "codes to manage different actions and functions inside the International Space Station. " \
                      "These codes are pre-authorized by the main control room at Earth unless it is mentioned.'" \
                      " " \
                      "On the second page of the book, you can find this: 'To open the hatch door you should have " \
                      "both two keys in the secured box. ATTENTION: you MUST have the outfit on you, before opening " \
                      "the hatch. Otherwise, your life is in fatal danger.'"
    box_f.add(book)

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

    corridor6 = gm.connect(hatch.north, lounge.south)
    door_d = gm.new_door(corridor6, name="door D")
    gm.add_fact("locked", door_d)
    gm.add_fact("match", key_6, door_d)

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
    gm.set_player(sleep_station)

    key_7 = gm.new(type='k', name="hearty key")
    key_7.infos.desc = "This key is shaped like a heart, not a normal key for a spaceship, ha ha ha..."
    gm.add_fact("match", key_7, box_c)
    gm.inventory.add(key_7)  # Add the object to the player's inventory.

    # gm.render(interactive=True)

    # quest = gm.new_quest_using_commands(['examine laptop',
    #                                      'open door A',
    #                                      'go south',
    #                                      'go east',
    #                                      'open box B',
    #                                      'take code key 1 from box B',
    #                                      'go west',
    #                                      'unlock box A with code key 1',
    #                                      'open box A',
    #                                      'take electronic key 1 from box A',
    #                                      'unlock door B with electronic key 1',
    #                                      'open door B',
    #                                      'go south',
    #                                      'examine box C',
    #                                      'unlock box C with hearty key',
    #                                      'open box C',
    #                                      'take digital key 1 from box C',
    #                                      'go east',
    #                                      'open box E',
    #                                      'take electronic key 2 from box E',
    #                                      'go west',
    #                                      'unlock door C with electronic key 2',
    #                                      'open door C',
    #                                      'go west',
    #                                      'unlock secured box with digital key 1',
    #                                      'open secured box',
    #                                      'take Secret Codes Handbook from secured box',
    #                                      'examine Secret Codes Handbook',
    #                                      'take code key 2 from secured box',
    #                                      'take digital key 2 from secured box',
    #                                      'go east',
    #                                      'go east',
    #                                      'unlock door D with code key 2',
    #                                      'open door D',
    #                                      'go south',
    #                                      'take outfit',
    #                                      'wear the outfit',
    #                                      'go north',
    #                                      'go west',
    #                                      'unlock exit box with digital key 2',
    #                                      'open exit box',
    #                                      'push exit push button',
    #                                      'go east',
    #                                      'go south',
    #                                      'go south'])

    arr = ['examine laptop',
           'check email',
           # 'open door A',
           # 'go south',
           # 'go east',
           # 'open box B',
           # 'take code key 1 from box B',
           # 'go west',
           # 'unlock box A with code key 1',
           # 'open box A',
           # 'take electronic key 1 from box A',
           # 'unlock door B with electronic key 1',
           # 'open door B',
           # 'go south',
           # 'examine box C',
           # 'unlock box C with hearty key',
           # 'open box C',
           # 'take digital key 1 from box C',
           # 'go east',
           # 'open box E',
           # 'take electronic key 2 from box E',
           # 'go west',
           # 'unlock door C with electronic key 2',
           # 'open door C',
           # 'go west',
           # 'unlock secured box with digital key 1',
           # 'open secured box',
           # 'take Secret Codes Handbook from secured box',
           # 'examine Secret Codes Handbook',
           # 'take code key 2 from secured box',
           # 'take digital key 2 from secured box',
           # 'go east',
           # 'go east',
           # 'unlock door D with code key 2',
           # 'open door D',
           # 'go south',
           # 'take outfit',
           # 'wear the outfit',
           # 'go north',
           # 'go west',
           # 'unlock exit box with digital key 2',
           # 'open exit box',
           # 'push exit push button',
           # 'go east',
           # 'go south',
           # 'go south'
           ]
    test_commands(gm, arr)


def test():
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
    gm = GameMaker(kb=kb, theme='Spaceship')

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

    surf_1 = gm.new(type='s', name='wall-mounted surface')
    surf_1.infos.desc = "This is a wall-mounted surface which different instruments are installed on this. These " \
                        "instruments are basically control various modules and doors in the shuttle."
    sleep_station.add(surf_1)

    laptop = gm.new(type='cpu', name='laptop')
    laptop.infos.desc = "This is your personal laptop which is attached to the surface of the table. You can do " \
                        "regular things with this, like check your emails, watch YouTube, Skype with family,etc." \
                        "Since you are here, we recommend you to check your emails. New missions are posted through " \
                        "emails. "
    surf_1.add(laptop)
    gm.add_fact("turned_off", laptop)

    # ===== Player and Inventory Design ================================================================================
    gm.set_player(sleep_station)

    gm.render(interactive=True)

    gm.record_quest()


def test_commands(game, arr):
    # with make_temp_directory() as tmpdir:
    #     game_file = self.compile(pjoin(tmpdir, "set_walkthrough.ulx"))
    #     env = textworld.start(game_file, infos=EnvInfos(last_action=True, intermediate_reward=True))
    #     state = env.reset()

    with make_temp_directory() as tmpdir:
        silent = False
        game_file = game.compile(pjoin(tmpdir, "test_game_1.ulx"))
        env = textworld.start(game_file, infos=EnvInfos(admissible_commands=True, intermediate_reward=True))
        env.reset()

        agent = textworld.agents.HumanAgent(autocompletion=True)
        agent.reset(env)

        if not silent:
            env.render(mode="human")

        try:
            for command in arr:
                print(command)
                game_state, reward, done = env.step(command)

                if not silent:
                    env.render()

                print("Available actions: {}\n".format(game_state.admissible_commands))
                print('==================================================')

        except KeyboardInterrupt:
            pass  # Stop the game.
        finally:
            env.close()


def spaceship_maker_level_medium_v1():
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
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
    sleep_station.add(surf_1)   # The card box contains nothing at this game

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
    gm.add_fact("locked", door_b)
    gm.add_fact("match", key_1, door_b)  # Tell the game 'Electronic key' is matching the 'door B''s lock

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
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
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
    sleep_station.add(surf_1)   # The card box contains nothing at this game

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
    gm.add_fact("locked", door_b)
    gm.add_fact("match", key_1, door_b)  # Tell the game 'Electronic key' is matching the 'door B''s lock

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
    gm.add_fact("locked", door_d)
    gm.add_fact("match", key_6, door_d)

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
    gm.set_player(sleep_station)
    # gm.set_player(us_lab)

    key_7 = gm.new(type='k', name="hearty key")
    key_7.infos.desc = "This key is shaped like a heart, not a normal key for a spaceship, ha ha ha..."
    gm.add_fact("match", key_7, box_c)
    gm.inventory.add(key_7)  # Add the object to the player's inventory.

    # gm.render(interactive=True)

    # gm.grammar = textworld.generator.make_grammar()


    # array_of_all_required_actions_to_win = ['examine laptop',
    #                                         'check email',
    #                                         'open door A',
    #                                         'go south',
    #                                         'go east',
    #                                         'open box B',
    #                                         'take code key 1 from box B',
    #                                         'go west',
    #                                         'unlock box A with code key 1',
    #                                         'open box A',
    #                                         'take electronic key 1 from box A',
    #                                         'unlock door B with electronic key 1',
    #                                         'open door B',
    #                                         'go south',
    #                                         'examine box C',
    #                                         'unlock box C with hearty key',
    #                                         'open box C',
    #                                         'take digital key 1 from box C',
    #                                         'go east',
    #                                         'open box E',
    #                                         'take electronic key 2 from box E',
    #                                         'go west',
    #                                         'unlock door C with electronic key 2',
    #                                         'open door C',
    #                                         'go west',
    #                                         'unlock secured box with digital key 1',
    #                                         'open secured box',
    #                                         'take Secret Codes Handbook from secured box',
    #                                         'read Secret Codes Handbook',
    #                                         'take code key 2 from secured box',
    #                                         'take digital key 2 from secured box',
    #                                         'go east',
    #                                         'go east',
    #                                         'unlock door D with code key 2',
    #                                         'open door D',
    #                                         'go south',
    #                                         'take outfit',
    #                                         'wear the outfit',
    #                                         'go north',
    #                                         'go west',
    #                                         'unlock exit box with digital key 2',
    #                                         'open exit box',
    #                                         'push exit push button',
    #                                         'go east',
    #                                         'go south',
    #                                         'go south']
    #
    # array_of_actions_for_a_fail_example1 = ['examine laptop',
    #                                         'check email',
    #                                         'open door A',
    #                                         'go south',
    #                                         'go east',
    #                                         'open box B',
    #                                         'take code key 1 from box B',
    #                                         'go west',
    #                                         'unlock box A with code key 1',
    #                                         'open box A',
    #                                         'take electronic key 1 from box A',
    #                                         'unlock door B with electronic key 1',
    #                                         'open door B',
    #                                         'go south',
    #                                         'examine box C',
    #                                         'unlock box C with hearty key',
    #                                         'open box C',
    #                                         'take digital key 1 from box C',
    #                                         'go east',
    #                                         'open box E',
    #                                         'take electronic key 2 from box E',
    #                                         'go west',
    #                                         'unlock door C with electronic key 2',
    #                                         'open door C',
    #                                         'go west',
    #                                         'unlock secured box with digital key 1',
    #                                         'open secured box',
    #                                         'take digital key 2 from secured box',
    #                                         'go east',
    #                                         'unlock exit box with digital key 2',
    #                                         'open exit box',
    #                                         'push exit push button',
    #                                         'go east',
    #                                         'go south',
    #                                         'go south']
    #
    # array_of_actions_for_a_fail_example2 = ['examine laptop',
    #                                         'check email',
    #                                         'open door A']

    quest_design(gm)

    # test_commands(gm, ['look', 'open door A', 'go south'])
    test_commands(gm, ['open door A', 'go north', 'go south'])
    # return quest_design(gm)

    corridor6 = gm.connect(hatch.north, lounge.south)
    door_d = gm.new_door(corridor6, name="door D")
    gm.add_fact("locked", door_d)
    gm.add_fact("match", key_6, door_d)

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
    gm.set_player(sleep_station)
    # gm.set_player(us_lab)

    key_7 = gm.new(type='k', name="hearty key")
    key_7.infos.desc = "This key is shaped like a heart, not a normal key for a spaceship, ha ha ha..."
    gm.add_fact("match", key_7, box_c)
    gm.inventory.add(key_7)  # Add the object to the player's inventory.

    # gm.render(interactive=True)

    # gm.grammar = textworld.generator.make_grammar()


    # array_of_all_required_actions_to_win = ['examine laptop',
    #                                         'check email',
    #                                         'open door A',
    #                                         'go south',
    #                                         'go east',
    #                                         'open box B',
    #                                         'take code key 1 from box B',
    #                                         'go west',
    #                                         'unlock box A with code key 1',
    #                                         'open box A',
    #                                         'take electronic key 1 from box A',
    #                                         'unlock door B with electronic key 1',
    #                                         'open door B',
    #                                         'go south',
    #                                         'examine box C',
    #                                         'unlock box C with hearty key',
    #                                         'open box C',
    #                                         'take digital key 1 from box C',
    #                                         'go east',
    #                                         'open box E',
    #                                         'take electronic key 2 from box E',
    #                                         'go west',
    #                                         'unlock door C with electronic key 2',
    #                                         'open door C',
    #                                         'go west',
    #                                         'unlock secured box with digital key 1',
    #                                         'open secured box',
    #                                         'take Secret Codes Handbook from secured box',
    #                                         'read Secret Codes Handbook',
    #                                         'take code key 2 from secured box',
    #                                         'take digital key 2 from secured box',
    #                                         'go east',
    #                                         'go east',
    #                                         'unlock door D with code key 2',
    #                                         'open door D',
    #                                         'go south',
    #                                         'take outfit',
    #                                         'wear the outfit',
    #                                         'go north',
    #                                         'go west',
    #                                         'unlock exit box with digital key 2',
    #                                         'open exit box',
    #                                         'push exit push button',
    #                                         'go east',
    #                                         'go south',
    #                                         'go south']
    #
    # array_of_actions_for_a_fail_example1 = ['examine laptop',
    #                                         'check email',
    #                                         'open door A',
    #                                         'go south',
    #                                         'go east',
    #                                         'open box B',
    #                                         'take code key 1 from box B',
    #                                         'go west',
    #                                         'unlock box A with code key 1',
    #                                         'open box A',
    #                                         'take electronic key 1 from box A',
    #                                         'unlock door B with electronic key 1',
    #                                         'open door B',
    #                                         'go south',
    #                                         'examine box C',
    #                                         'unlock box C with hearty key',
    #                                         'open box C',
    #                                         'take digital key 1 from box C',
    #                                         'go east',
    #                                         'open box E',
    #                                         'take electronic key 2 from box E',
    #                                         'go west',
    #                                         'unlock door C with electronic key 2',
    #                                         'open door C',
    #                                         'go west',
    #                                         'unlock secured box with digital key 1',
    #                                         'open secured box',
    #                                         'take digital key 2 from secured box',
    #                                         'go east',
    #                                         'unlock exit box with digital key 2',
    #                                         'open exit box',
    #                                         'push exit push button',
    #                                         'go east',
    #                                         'go south',
    #                                         'go south']
    #
    # array_of_actions_for_a_fail_example2 = ['examine laptop',
    #                                         'check email',
    #                                         'open door A']

    quest_design(gm)

    # test_commands(gm, ['look', 'open door A', 'go south'])
    test_commands(gm, ['open door A', 'go north', 'go south'])
    # return quest_design(gm)


def spaceship_maker_level_medium_v2():
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
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
    sleep_station.add(surf_1)   # The card box contains nothing at this game

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

    cloth = gm.new(type='l', name="outfit")
    us_lab.add(cloth)
    gm.add_fact("takenoff", cloth)
    gm.add_fact("clean", cloth)

    corridor_1 = gm.connect(sleep_station.south, us_lab.north)
    door_a = gm.new_door(corridor_1, name="door A")
    gm.add_fact("closed", door_a)

    # # ===== European Module Design =====================================================================================
    # european_module = gm.new_room("European Module")
    # european_module.infos.desc = "This room belongs to European scientists. Isn't it cool? what do they research? " \
    #                              "well, we can explore it later... For now, there is a key code here. This code " \
    #                              "opens the box in the next room and consequently takes you to the next stage. So, " \
    #                              "explore the table to find the key."
    #
    # surf_2 = gm.new(type='s', name='table')
    # surf_2.infos.desc = "This is a simple table located in the middle of the room. Let's take a look at it..."
    # european_module.add(surf_2)
    #
    # box_b = gm.new(type='c', name="box B")
    # box_b.infos.desc = "This a regular box, keeps the key to open box A."
    # surf_2.add(box_b)
    # gm.add_fact("closed", box_b)
    #
    # key_2 = gm.new(type='k', name="code key 1")
    # key_2.infos.desc = "This key is in fact a digital code which opens the box in the US Lab area. The code, " \
    #                    "in fact, is written on a piece of paper."
    # box_b.add(key_2)
    # gm.add_fact("match", key_2, box_a)
    #
    # chair_1 = gm.new(type='s', name='chair')
    # chair_1.infos.desc = "this is a dark-gray chair which is developed to be used in space."
    # european_module.add(chair_1)
    #
    # corridor_2 = gm.connect(us_lab.east, european_module.west)
    # door_b = gm.new_door(corridor_2, name="door B")
    # gm.add_fact("closed", door_b)

    # ===== Player and Inventory Design ================================================================================
    gm.set_player(us_lab)

    quest_design_2(gm)

    return gm


def quest_design_2(game):
    quests = []

    # 1. Is the Player performing successful in the Sleeping Station
    win_quest = EventCondition(conditions={
        game.new_fact("at", game._entities['P'], game._entities['r_0'])
    })
    quests.append(Quest(win_events=[win_quest], fail_events=[], reward=0))

    fail_quest = EventCondition(conditions={
        game.new_fact("event", game._entities['P'], game._entities['r_0']),
        game.new_fact("at", game._entities['P'], game._entities['r_1']),
        game.new_fact("open", game._entities['d_0']),
        game.new_fact("unread/e", game._entities['cpu_0']),
    })
    win_quest = EventCondition(conditions={
        game.new_fact("event", game._entities['P'], game._entities['r_0']),
        game.new_fact("at", game._entities['P'], game._entities['r_1']),
        game.new_fact("open", game._entities['d_0']),
        game.new_fact("read/e", game._entities['cpu_0']),
    })
    quests.append(Quest(win_events=[win_quest], fail_events=[fail_quest]))

    # 2.
    win_quest = EventCondition(conditions={game.new_fact("worn", game._entities['l_0'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))

    game.quests = quests

    return game.build()


def quest_design(game):
    quests = []

    # 1. Player is in the Sleeping Station
    win_quest = EventCondition(conditions={game.new_fact("read/e", game._named_entities['laptop'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))
    tp = EventCondition(conditions={game.new_fact("unread/e", game._named_entities['laptop'])})
    fail_quest = tp
    quests.append(Quest(win_events=[], fail_events=[fail_quest]))

    # 2. Player is in US LAB to find Electronic Key 1
    win_quest = EventCondition(conditions={game.new_fact("in", game._named_entities['electronic key 1'], game._entities['I'])})
    quests.append(Quest(win_events=[win_quest], fail_events=[]))

    # # 3. Player is in Russian Module and take digital Key 1 and/or push the button
    # win_quest = Event(conditions={game.new_fact("in", game._named_entities['digital key 1'], game._entities['I'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    # win_quest = Event(conditions={game.new_fact("pushed", game._named_entities['exit push button']),
    #                               game.new_fact("worn", game._named_entities['outfit'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    # fail_quest = Event(conditions={game.new_fact("pushed", game._named_entities['exit push button']),
    #                                game.new_fact("takenoff", game._named_entities['outfit'])})
    # quests.append(Quest(win_events=[], fail_events=[fail_quest]))
    #
    # # 4. Player is the Control Module and take Electronic Key 2
    # win_quest = Event(conditions={game.new_fact("in", game._named_entities['digital key 2'], game._entities['I'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    #
    # # 5. Player reads the Secret Code book at Control Module
    # win_quest = Event(conditions={game.new_fact("read/t", game._named_entities['Secret Codes Handbook'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    #
    # # 6. Player is in Hatch room and wears the cloth
    # win_quest = Event(conditions={game.new_fact("worn", game._named_entities['outfit'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    #
    # # 7. Player goes outside
    # win_quest = Event(conditions={game.new_fact("at", game._entities['P'], game._named_entities['Outside'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))

    game.quests = quests

    _game = game.build()

    return _game


def testFW_easyGame():
    # GameMaker object for handcrafting text-based games.
    kb = KnowledgeBase.load(target_dir=PATH)
    gm = GameMaker(kb=kb, theme='Spaceship')

    # ===== Sleep Station Design =======================================================================================
    sleep_station = gm.new_room("Sleep Station")

    surf_1 = gm.new(type='s', name='vertical desk')  # surf_1 is a table (supporter) in the Sleep Station.
    sleep_station.add(surf_1)  # The card box contains nothing at this game
    laptop = gm.new(type='cpu', name='laptop')
    surf_1.add(laptop)
    # gm.add_fact('turned_off', laptop)
    gm.add_fact('unread/e', laptop)

    # ===== US LAB Design ==============================================================================================
    us_lab = gm.new_room("US LAB")

    # ===== European Module Design =====================================================================================
    # european_module = gm.new_room("European Module")

    corridor_1 = gm.connect(sleep_station.south, us_lab.north)
    door_a = gm.new_door(corridor_1, name="door A")
    gm.add_fact("closed", door_a)
    # corridor_2 = gm.connect(sleep_station.east, european_module.west)
    # door_b = gm.new_door(corridor_2, name="door B")
    # gm.add_fact("closed", door_b)
    # gm.add_fact("closed", door_a, door_b)

    gm.set_player(sleep_station)
    gm.render(interactive=True)

    quests = []

    # # A. The EVENT solution
    # # ------------------------------------------
    # # 1. Player is in the Sleeping Station
    # win_quest = Event(conditions={gm.new_fact("read/e", gm._named_entities['laptop'])})
    # fail_quest = Event(conditions={gm.new_fact("unread/e", gm._named_entities['laptop']),
    #                                gm.new_fact("open", gm._named_entities['door A'])})
    # quests.append(Quest(win_events=[win_quest], fail_events=[fail_quest]))
    # gm.quests = quests

    # # B. The NEW_EVENT_USING_COMMANDS solution
    # # ------------------------------------------
    # win_quest = gm.new_event_using_commands(['open door A'])
    # quests.append(Quest(win_events=[win_quest], fail_events=[]))
    # gm.quests = quests

    # # C. The NEW_QUEST_USING_COMMANDS solution
    # # ------------------------------------------
    # quest = gm.new_quest_using_commands(['open door A'])
    # gm.quests = [quest]

    # B. The RECORD_QUEST solution
    # ------------------------------------------
    a = gm.record_quest()

    gm.test()


def create_world(options: Optional[GameOptions]):
    kb = KnowledgeBase.load(target_dir=PATH)
    options = options or GameOptions()
    options.grammar.theme = 'Spaceship'
    options.kb = kb
    options.seeds = g_rng.seed

    rngs = options.rngs
    rng_map = rngs['map']
    rng_objects = rngs['objects']
    rng_grammar = rngs['grammar']
    rng_quest = rngs['quest']

    door_states = ["open", "closed", "locked"]

    # Generate map.
    map_ = textworld.generator.make_map(n_rooms=options.nb_rooms, rng=rng_map, possible_door_states=door_states)
    world = World.from_map(map_)

    # Randomly place the player.
    starting_room = None
    if len(world.rooms) > 1:
        starting_room = rng_map.choice(world.rooms)

    world.set_player_room(starting_room)


if __name__ == "__main__":
    # spaceship_maker_level_easy()
    # spaceship_maker_level_medium()
    # test()
    # testFW_easyGame()
    # spaceship_maker_level_medium_v1()
    game = spaceship_maker_level_medium_v2()
    test_commands(game, [
        'open door A',
        'go north',
        'check laptop for email',
        'check laptop for email',
        'go south',
        'take outfit',
        'wear the outfit',
    ])

