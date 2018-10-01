from os.path import join as pjoin

import textworld

from textworld import g_rng  # Global random generator.
from textworld import GameMaker
from textworld.utils import make_temp_directory


def test_food():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    apple = M.new("f", name="apple")
    M.add_fact("edible", apple)
    raw_meat = M.new("f", name="raw meat")
    table = M.new("table", name="table")
    room.add(table)
    table.add(apple)
    M.inventory.add(raw_meat)

    with make_temp_directory(prefix="test_food") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()

        assert "eat raw meat" not in game_state.admissible_commands
        game_state, _, _ = env.step("eat raw meat")
        assert "plainly inedible" in game_state.feedback

        assert "eat apple" not in game_state.admissible_commands
        game_state, _, _ = env.step("eat apple")
        assert "need to take" in game_state.feedback

        assert "take apple from table" in game_state.admissible_commands
        game_state, _, _ = env.step("take apple from table")

        assert "eat apple" in game_state.admissible_commands
        game_state, _, _ = env.step("eat apple")
        assert "You eat the apple. Not bad" in game_state.feedback

        assert "eat apple" not in game_state.admissible_commands
        game_state, _, _ = env.step("eat apple")
        assert "can't see" in game_state.feedback


def test_food_constraints():
    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)
    apple = M.new("f", name="apple")
    M.add_fact("eaten", apple)
    assert M.validate()

    # Eaten food should be nowhere.
    M.inventory.add(apple)
    assert not M.validate()
