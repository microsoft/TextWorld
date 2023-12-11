from functools import partial

import textworld
import textworld.gym
from textworld import EnvInfos
from textworld.utils import make_temp_directory
from textworld.envs import JerichoEnv
from textworld.envs.batch.batch_env import AsyncBatchEnv, SyncBatchEnv


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
        env = textworld.gym.make(env_id)
        env.reset()
        # env.close()
        del env


def test_seed():
    batch_size = 4
    env_options = EnvInfos(inventory=True, description=True, admissible_commands=True)
    env_fns = [partial(JerichoEnv, env_options) for _ in range(batch_size)]

    env = SyncBatchEnv(env_fns)
    seeds = env.seed(1234)
    for seed, env_ in zip(seeds, env.envs):
        assert seed == env_._seed

    env.seed(range(batch_size))
    for seed, env_ in zip(range(batch_size), env.envs):
        assert seed == env_._seed

    env.close()

    env = AsyncBatchEnv(env_fns)
    seeds = env.seed(1234)
    for seed, env_ in zip(seeds, env.envs):
        assert seed == env_.get_sync("_seed")

    env.seed(range(batch_size))
    for seed, env_ in zip(range(batch_size), env.envs):
        assert seed == env_.get_sync("_seed")

    env.close()
