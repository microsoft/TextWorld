from os.path import join as pjoin

import textworld

from textworld import g_rng  # Global random generator.
from textworld import GameMaker
from textworld.utils import make_temp_directory


def test_chest():
    g_rng.set_seed(20180905)  # Make the generation process reproducible.

    M = GameMaker()
    bank = M.new_room("Bank")
    M.set_player(bank)

    money = M.new("o", name="gold bar")
    safe = M.new("chest", name="safe")
    M.add_fact("closed", safe)
    bank.add(safe)
    safe.add(money)

    with make_temp_directory(prefix="test_chest") as tmpdir:
        game_file = M.compile(pjoin(tmpdir, "game.ulx"))
        env = textworld.start(game_file)
        env.activate_state_tracking()
        game_state = env.reset()

        assert "open safe" in game_state.admissible_commands
        game_state, _, _ = env.step("open safe")
        assert "You open the" in game_state.feedback
        assert "open safe" not in game_state.admissible_commands
        assert "close safe" in game_state.admissible_commands
        game_state, _, _ = env.step("close safe")
        assert "You close the" in game_state.feedback
        assert "close safe" not in game_state.admissible_commands

        # Already open/closed.
        game_state, _, _ = env.step("open safe")
        game_state, _, _ = env.step("open safe")
        assert "already open" in game_state.feedback
        game_state, _, _ = env.step("close safe")
        game_state, _, _ = env.step("close safe")
        assert "already close" in game_state.feedback

        game_state, _, _ = env.step("open safe")
        game_state, _, _ = env.step("take gold bar from safe")
        assert "gold bar" in game_state.inventory
