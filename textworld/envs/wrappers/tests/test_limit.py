import textworld
from textworld.envs.wrappers import Limit
from textworld.generator import compile_game
from textworld.utils import make_temp_directory


def test_limit_wrapper():
    # Make a game for testing purposes.
    max_episode_steps = 7

    num_nodes = 3
    num_items = 10
    options = textworld.GameOptions()
    options.seeds = 1234
    options.nb_rooms = num_nodes
    options.nb_objects = num_items
    options.quest_length = 3
    options.grammar.theme = "house"
    options.grammar.include_adj = True
    game = textworld.generator.make_game(options)

    game_name = "test_limit_wrapper"
    with make_temp_directory(prefix=game_name) as tmpdir:
        options.path = tmpdir
        game_file = compile_game(game, options)

        env = textworld.start(game_file)
        env = Limit(env, max_episode_steps)
        state = env.reset()

        done = False
        assert state["moves"] == 0
        for no_step in range(1, max_episode_steps + 1):
            assert not done
            state, score, done = env.step("wait")
            assert state["moves"] == no_step

        assert done
