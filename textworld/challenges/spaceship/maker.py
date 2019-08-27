from textworld.challenges.spaceship import GameMaker


def spaceship_maker():
    # GameMaker object for handcrafting text-based games.
    gm = GameMaker(theme='Spaceship')
    # gm = GameMaker()

    # ===== Sleep Station Design =======================================================================================
    sleep_station = gm.new_room("Sleep Station")

    sleep_bag = gm.new(type='c', name="Sleeping Bag")       # Provide the type and the name of the object.
    sleep_bag.desc = "cool! You can sleep in a comfy bag."  # Text to display when issuing command "examine note".
    sleep_station.add(sleep_bag)  # Sleeping bag is fixed in place in the Sleep Station.
    gm.add_fact("open", sleep_bag)

    card_box = gm.new(type='c')   # Card box is a container which is fixed in place in the Sleep Station.
    card_box.desc = "It is empty."
    sleep_station.add(card_box)   # The card box contains nothing at this game
    gm.add_fact("closed", card_box)

    # ===== US LAB Design ==============================================================================================
    us_lab = gm.new_room("US LAB")
    key = gm.new(type='k', name="Electronic key")
    key.desc = "This key opens the door into the modules area. " \
               "In this space craft, the gravity is not a challenge. Thus, you can find things on the floor."
    us_lab.add(key)  # When added directly to a room, portable objects are put on the floor.

    corridor1 = gm.connect(sleep_station.south, us_lab.north)
    doorA = gm.new_door(corridor1, name="door A")
    gm.add_fact("closed", doorA)  # Add a fact about the door, e.g. here it is closed.
    # gm.render()

    # ===== Russian Module Design ======================================================================================
    russian_module = gm.new_room("Russian Module")
    supporter = gm.new(type='s')  # When not provided, names are automatically generated.
    russian_module.add(supporter)  # Supporters are fixed in place.
    key_code = gm.new(type='k', name="Electronic key")
    key_code.desc = "This key is in fact a digital code which opens the secured box in the control modules area. " \
                    "The code, in fact, is written on the supporter."
    supporter.add(key_code)

    corridor2 = gm.connect(us_lab.south, russian_module.north)
    doorB = gm.new_door(corridor2, name="door B")
    gm.add_fact("locked", doorB)
    gm.add_fact("match", key, doorB)  # Tell the game 'Electronic key' is matching the 'door B''s lock
    # gm.render()

    # ===== Control Module Design ======================================================================================
    control_module = gm.new_room("Control Module")
    secured_box = gm.new(type='c', name='Secured box')  # When not provided, names are automatically generated.
    secured_box.desc = "This box is highly secured with a complex code that is in one of the modules in the craft. " \
                       "To open the box, you should just find that code key."
    gm.add_fact("locked", secured_box)
    gm.add_fact("match", key_code, secured_box)
    secured_box.desc = "The Secret Codes Handbook is in this box."
    control_module.add(secured_box)  # Supporters are fixed in place.
    book = gm.new(type='o', name='Secret Codes Handbook')  # New portable object with a randomly generated name.
    secured_box.add(book)

    corridor3 = gm.connect(russian_module.west, control_module.east)
    doorC = gm.new_door(corridor3, name='door C')
    gm.add_fact("open", doorC)
    # gm.render()

    # ===== Player and Inventory Design ================================================================================
    gm.set_player(sleep_station)

    pencil = gm.new(type='o', name='pencil')  # New portable object with a randomly generated name.
    gm.inventory.add(pencil)  # Add the object to the player's inventory.
    # gm.render()

    quest = gm.record_quest()


if __name__ == "__main__":
    spaceship_maker()
