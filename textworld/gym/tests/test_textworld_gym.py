import os

import gym

import textworld
import textworld.gym
from textworld import EnvInfos
from textworld.utils import make_temp_directory


def test_register_game():
    with make_temp_directory() as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.seeds = 1234
        gamefile, game = textworld.make(options)
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True)

        env_id = textworld.gym.register_game(gamefile, env_options, name="test-single")
        env = gym.make(env_id)
        obs, infos = env.reset()
        assert len(infos) == len(env_options)

        for cmd in game.main_quest.commands:
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1


def test_register_zmachine_game():
    with make_temp_directory() as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.seeds = 1234
        options.file_ext = ".z8"
        gamefile, game = textworld.make(options)
        os.remove(gamefile.replace(".z8", ".json"))  # Simulate an existing Z-Machine game.
        env_options = EnvInfos()

        env_id = textworld.gym.register_game(gamefile, env_options, name="test-zmachine")
        env = gym.make(env_id)
        obs, infos = env.reset()
        assert len(infos) == len(env_options)

        for cmd in game.main_quest.commands:
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1


def test_register_games():
    with make_temp_directory() as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.seeds = 1234
        gamefile1, game1 = textworld.make(options)
        options.seeds = 4321
        gamefile2, game2 = textworld.make(options)
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True)

        env_id = textworld.gym.register_games([gamefile1, gamefile2], env_options, name="test-multi")
        env = gym.make(env_id)
        env.seed(2)  # Make game2 starts on the first reset call.

        obs, infos = env.reset()
        assert len(infos) == len(env_options)

        for cmd in game2.main_quest.commands:
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1

        obs, infos = env.reset()
        assert len(infos) == len(env_options)
        for cmd in game1.main_quest.commands:
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1

        obs1, infos = env.reset()
        obs2, infos = env.reset()
        assert obs1 != obs2


def test_batch():
    batch_size = 5
    with make_temp_directory() as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.seeds = 1234
        gamefile, game = textworld.make(options)

        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True)
        env_id = textworld.gym.register_games([gamefile], env_options, name="test-batch")
        env_id = textworld.gym.make_batch(env_id, batch_size)
        env = gym.make(env_id)

        obs, infos = env.reset()
        assert len(obs) == batch_size
        assert len(set(obs)) == 1  # All the same game.
        assert len(infos) == len(env_options)
        for values in infos.values():
            assert len(values) == batch_size

        for cmd in game.main_quest.commands:
            obs, scores, dones, infos = env.step([cmd] * batch_size)

        env.close()

        assert all(dones)
        assert all(score == 1 for score in scores)


def test_batch_parallel():
    batch_size = 5
    with make_temp_directory() as tmpdir:
        options = textworld.GameOptions()
        options.path = tmpdir
        options.seeds = 1234
        gamefile, game = textworld.make(options)

        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True)
        env_id = textworld.gym.register_game(gamefile, env_options, name="test-batch-parallel")
        env_id = textworld.gym.make_batch(env_id, batch_size, parallel=True)
        env = gym.make(env_id)

        obs, infos = env.reset()
        assert len(obs) == batch_size
        assert len(set(obs)) == 1  # All the same game.
        assert len(infos) == len(env_options)
        for values in infos.values():
            assert len(values) == batch_size

        for cmd in game.main_quest.commands:
            obs, scores, dones, infos = env.step([cmd] * batch_size)

        env.close()

        assert all(dones)
        assert all(score == 1 for score in scores)
