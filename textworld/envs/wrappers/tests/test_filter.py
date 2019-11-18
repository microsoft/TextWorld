import textworld
from textworld import EnvInfos
from textworld.envs.wrappers import Filter
from textworld.generator import compile_game
from textworld.utils import make_temp_directory


def test_filter_wrapper():
    # Make a game for testing purposes.
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

    game_name = "test_filter_wrapper"
    with make_temp_directory(prefix=game_name) as tmpdir:
        options.path = tmpdir
        game_file = compile_game(game, options)

        env_infos = EnvInfos()
        for attr in env_infos.__slots__:
            if attr == "extras":
                continue  # Skip since it's not a boolean attribute.

            setattr(env_infos, attr, True)

        env = textworld.start(game_file, env_infos)
        assert len(env_infos) == len(env_infos.__slots__) - 1
        assert len(env_infos) == len(env_infos.basics)

        env = Filter(env)
        _, infos = env.reset()

        for attr in env_infos.basics:
            assert attr in infos
