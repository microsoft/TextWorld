from os.path import join as pjoin

import textworld

from textworld import g_rng  # Global random generator.
from textworld import GameMaker
from textworld.utils import make_temp_directory


def test_stool():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    concert = M.new_room("Concert")
    M.set_player(concert)

    stage = M.new("table", name="stage")
    stool = M.new("stool", name="stool")
    water = M.new("o", name="bottle of water")
    mic = M.new("o", name="microphone")
    concert.add(stage)
    stage.add(stool)
    stool.add(water)
    stool.add(mic)

    with make_temp_directory(prefix="test_stool") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()

        assert "take microphone from stool" in game_state.admissible_commands
        assert "take bottle of water from stool" in game_state.admissible_commands
        assert "take stool from stage" in game_state.admissible_commands
        game_state, _, _ = env.step("take stool from stage")
        assert "stool" in game_state.inventory
        assert "    a microphone" in game_state.inventory
        assert "    a bottle of water" in game_state.inventory

        game_state, _, _ = env.step("take microphone from stool")
        assert "    a microphone" not in game_state.inventory
        assert "microphone" in game_state.inventory

        game_state, _, _ = env.step("drop stool")
        assert "stool" not in game_state.inventory
        assert "bottle of water" not in game_state.inventory

        game_state, _, _ = env.step("take bottle of water from stool")
        assert "bottle of water" in game_state.inventory

        game_state, _, _ = env.step("examine stool")
        assert "nothing" in game_state.feedback

        game_state, _, _ = env.step("put microphone on stool")
        assert "microphone" not in game_state.inventory


def test_nested_stools():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    room = M.new_room("room")
    M.set_player(room)

    block1 = M.new("stool", name="large block")
    block2 = M.new("stool", name="medium block")
    block3 = M.new("stool", name="small block")

    room.add(block1)
    M.inventory.add(block2)
    M.inventory.add(block3)

    with make_temp_directory(prefix="test_nested_stools") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()

        assert "put small block on medium block" not in game_state.admissible_commands
        game_state, _, _ = env.step("put small block on medium block")
        assert "cannot put" in game_state.feedback
        assert "small block" in game_state.inventory

        assert "put small block on large block" not in game_state.admissible_commands
        game_state, _, _ = env.step("put small block on large block")
        assert "cannot put" in game_state.feedback
        assert "small block" in game_state.inventory
