import gym

import textworld
import textworld.gym
from textworld import EnvInfos
from textworld.utils import make_temp_directory


def test_batch_env():
    batch_size = 4
    max_episode_steps = 13
    with make_temp_directory() as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.seeds = 1234
        options.file_ext = ".ulx"
        game_file1, game1 = textworld.make(options)
        options.seeds = 4321
        options.file_ext = ".z8"
        game_file2, game2 = textworld.make(options)

        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True)
        env_id = textworld.gym.register_games([game_file1, game_file1, game_file2, game_file2],
                                              request_infos=env_options,
                                              batch_size=batch_size,
                                              max_episode_steps=max_episode_steps,
                                              name="test-auto-reset",
                                              asynchronous=True,
                                              auto_reset=True)
        env = gym.make(env_id)
        env.reset()
        # env.close()
        del env
        print("OKAY")
