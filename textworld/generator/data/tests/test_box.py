from os.path import join as pjoin

import textworld

from textworld import g_rng  # Global random generator.
from textworld import GameMaker
from textworld.utils import make_temp_directory


def test_box():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    obj1 = M.new("o", name="obj1")
    obj2 = M.new("o", name="obj2")
    box = M.new("box", name="box")
    M.add_fact("open", box)
    box.add(obj2)
    M.inventory.add(box, obj1)

    with make_temp_directory(prefix="test_box") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()
        
        # box in the inventory
        #     open/close/insert into/take from
        #     insert/drop/put portable object from the box (not allowed)
        #     drop box
        assert "insert obj1 into box" in game_state.admissible_commands
        game_state, _, _ = env.step("insert obj1 into box")
        assert "    an obj1" in game_state.inventory

        assert "drop obj1" not in game_state.admissible_commands
        game_state, _, _ = env.step("drop obj1")
        assert "    an obj1" in game_state.inventory

        assert "close box" in game_state.admissible_commands
        game_state, _, _ = env.step("close box")
        assert "close the box" in game_state.feedback
        assert "    an obj1" not in game_state.inventory

        assert "take obj1 from box" not in game_state.admissible_commands
        game_state, _, _ = env.step("take obj1 from box")
        assert "obj1" not in game_state.inventory

        assert "open box" in game_state.admissible_commands
        game_state, _, _ = env.step("open box")
        assert "open the box" in game_state.feedback

        assert "take obj1 from box" in game_state.admissible_commands
        game_state, _, _ = env.step("take obj1 from box")
        assert "    an obj1" not in game_state.inventory
        assert "  an obj1" in game_state.inventory

        assert "drop box" in game_state.admissible_commands
        game_state, _, _ = env.step("drop box")
        assert "obj2" not in game_state.inventory
        assert "box" not in game_state.inventory

        # box on the floor
        #     open/close/insert into box/take from the box
        #     take the box
        assert "take obj2 from box" in game_state.admissible_commands
        game_state, _, _ = env.step("take obj2 from box")
        assert "obj2" in game_state.inventory

        assert "insert obj1 into box" in game_state.admissible_commands
        game_state, _, _ = env.step("insert obj1 into box")
        assert "obj1" not in game_state.inventory

        assert "close box" in game_state.admissible_commands
        game_state, _, _ = env.step("close box")
        assert "take obj1 from box" not in game_state.admissible_commands

        assert "take box" in game_state.admissible_commands
        game_state, _, _ = env.step("take box")
        assert "box" in game_state.inventory
        

def test_box2():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    obj1 = M.new("o", name="obj1")
    table = M.new("table", name="table")
    chest = M.new("chest", name="chest")
    box = M.new("box", name="box")
    M.add_fact("closed", chest)
    M.add_fact("closed", box)
    chest.add(box)
    room.add(chest, table)
    box.add(obj1)

    with make_temp_directory(prefix="test_box") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()

        # box in a fixed in place container aka a chest
        #     open/close/insert into/take from
        assert "open box" not in game_state.admissible_commands
        game_state, _, _ = env.step("open box")
        assert "can't" in game_state.feedback
        
        assert "open chest" in game_state.admissible_commands
        game_state, _, _ = env.step("open chest")

        assert "open box" in game_state.admissible_commands
        game_state, _, _ = env.step("open box")

        game_state, _, _ = env.step("examine box")
        assert "obj1" in game_state.feedback

        assert "take obj1 from box" in game_state.admissible_commands
        game_state, _, _ = env.step("take obj1 from box")
        assert "obj1" in game_state.inventory

        assert "take box from chest" in game_state.admissible_commands
        game_state, _, _ = env.step("take box from chest")
        assert "box" in game_state.inventory

        assert "put box on table" in game_state.admissible_commands
        game_state, _, _ = env.step("put box on table")
        assert "box" not in game_state.inventory

        # box in a fixed in place supporter aka a table
        #     open/close/insert into box/take from the box
        #     take the box
        assert "insert obj1 into box" in game_state.admissible_commands
        game_state, _, _ = env.step("insert obj1 into box")
        assert "obj1" not in game_state.inventory

        assert "close box" in game_state.admissible_commands
        game_state, _, _ = env.step("close box")
        assert "take obj1 from box" not in game_state.admissible_commands


def test_nested_boxes():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    doll1 = M.new("box", name="big Russian doll")
    doll2 = M.new("box", name="medium Russian doll")
    doll3 = M.new("box", name="small Russian doll")
    ball = M.new("o", name="ball")
    stool = M.new("stool", name="stool")

    M.add_fact("open", doll1)
    M.add_fact("open", doll2)
    M.add_fact("closed", doll3)
    room.add(doll1)
    room.add(stool)
    M.inventory.add(doll2)
    M.inventory.add(doll3)
    M.inventory.add(ball)

    with make_temp_directory(prefix="test_nested_boxes") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()

        assert "insert small Russian doll into medium Russian doll" not in game_state.admissible_commands
        game_state, _, _ = env.step("insert small Russian doll into medium Russian doll")
        assert "cannot insert" in game_state.feedback
        assert "small Russian doll" in game_state.inventory

        assert "insert small Russian doll into big Russian doll" not in game_state.admissible_commands
        game_state, _, _ = env.step("insert small Russian doll into big Russian doll")
        assert "cannot insert" in game_state.feedback
        assert "small Russian doll" in game_state.inventory

        assert "put small Russian doll on stool" not in game_state.admissible_commands
        game_state, _, _ = env.step("put small Russian doll on stool")
        assert "cannot put" in game_state.feedback
        assert "small Russian doll" in game_state.inventory
