import os
import glob
import shutil
import tempfile
import unittest
from os.path import join as pjoin

import pytest

import textworld
import textworld.gym
from textworld import EnvInfos
from textworld.utils import make_temp_directory


@pytest.mark.filterwarnings("ignore::jericho.UnsupportedGameWarning")
class TestGymIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = pjoin(tempfile.mkdtemp(prefix="test_textworld_gym"), "")
        options = textworld.GameOptions()
        options.path = cls.tmpdir
        options.seeds = 1234
        cls.gamefile1, cls.game1 = textworld.make(options)
        options.seeds = 4321
        cls.gamefile2, cls.game2 = textworld.make(options)

        options.file_ext = ".z8"
        options.seeds = 1234
        cls.gamefile1_z8, _ = textworld.make(options)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        self.before_tw = glob.glob(pjoin(tempfile.gettempdir(), "tw_*"))
        self.before_mlglk = glob.glob(pjoin(tempfile.gettempdir(), "mlglk_*"))

    def tearDown(self):
        # Check for file leaks.
        after_tw = glob.glob(pjoin(tempfile.gettempdir(), "tw_*"))
        after_mlglk = glob.glob(pjoin(tempfile.gettempdir(), "mlglk_*"))
        assert set(after_tw) == set(self.before_tw)
        assert set(after_mlglk) == set(self.before_mlglk)

    def test_register_game(self):
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True,
                               extras=["walkthrough"])

        env_id = textworld.gym.register_game(self.gamefile1, env_options, name="test-single")
        env = textworld.gym.make(env_id)
        obs, infos = env.reset()
        assert len(infos) == len(env_options)

        for cmd in infos.get("extra.walkthrough"):
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1

        env.close()

    def test_registering_zmachine_game(self):
        with make_temp_directory() as tmpdir:
            options = textworld.GameOptions()
            options.path = tmpdir
            options.seeds = 1234
            options.file_ext = ".z8"
            gamefile, game = textworld.make(options)
            os.remove(gamefile.replace(".z8", ".json"))  # Simulate an non-TextWorld Z-Machine game.
            env_options = EnvInfos(extras=["walkthrough"])

            env_id = textworld.gym.register_game(gamefile, env_options, name="test-zmachine")
            env = textworld.gym.make(env_id)
            obs, infos = env.reset()
            assert len(infos) == len(env_options)

            for cmd in game.metadata["walkthrough"]:
                obs, score, done, infos = env.step(cmd)

            assert done
            assert score == 1

            env.close()

    def test_register_games(self):
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True,
                               extras=["walkthrough"])

        env_id = textworld.gym.register_games([self.gamefile1, self.gamefile2],
                                              env_options, name="test-multi")
        env = textworld.gym.make(env_id)
        env.seed(2)  # Make game2 starts on the first reset call.

        obs, infos = env.reset()
        assert len(infos) == len(env_options)

        for cmd in self.game2.metadata["walkthrough"]:
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1

        obs, infos = env.reset()
        assert len(infos) == len(env_options)
        for cmd in self.game1.metadata["walkthrough"]:
            obs, score, done, infos = env.step(cmd)

        assert done
        assert score == 1

        obs1, infos = env.reset()
        obs2, infos = env.reset()
        assert obs1 != obs2

        env.close()

    def test_batch_sync(self):
        batch_size = 5
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True,
                               extras=["walkthrough"])
        env_id = textworld.gym.register_games([self.gamefile1, self.gamefile1_z8],
                                              request_infos=env_options,
                                              batch_size=batch_size,
                                              name="test-batch",
                                              asynchronous=False)
        env = textworld.gym.make(env_id)

        obs, infos = env.reset()
        assert len(obs) == batch_size
        assert len(set(obs)) == 1  # All the same game.
        assert len(infos) == len(env_options)
        for values in infos.values():
            assert len(values) == batch_size

        # Sending single command should raise assertion.
        with pytest.raises(AssertionError):
            obs, scores, dones, infos = env.step("wait")

        # Sending not engough commands should raise assertion.
        with pytest.raises(AssertionError):
            obs, scores, dones, infos = env.step(["wait"] * (batch_size - 1))

        for cmds in zip(*infos.get("extra.walkthrough")):
            obs, scores, dones, infos = env.step(cmds)

        env.close()

        assert all(dones)
        assert all(score == 1 for score in scores)

    def test_batch_async(self):
        batch_size = 5
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True,
                               extras=["walkthrough"])
        env_id = textworld.gym.register_games([self.gamefile1, self.gamefile1_z8],
                                              request_infos=env_options,
                                              batch_size=batch_size,
                                              name="test-batch-parallel",
                                              asynchronous=True)
        env = textworld.gym.make(env_id)

        obs, infos = env.reset()
        assert len(obs) == batch_size
        assert len(set(obs)) == 1  # All the same game.
        assert len(infos) == len(env_options)
        for values in infos.values():
            assert len(values) == batch_size

        # Sending single command should raise assertion.
        with pytest.raises(AssertionError):
            obs, scores, dones, infos = env.step("wait")

        # Sending not engough commands should raise assertion.
        with pytest.raises(AssertionError):
            obs, scores, dones, infos = env.step(["wait"] * (batch_size - 1))

        for cmds in zip(*infos.get("extra.walkthrough")):
            obs, scores, dones, infos = env.step(cmds)

        env.close()

        assert all(dones)
        assert all(score == 1 for score in scores)

    def test_auto_reset(self):
        batch_size = 4
        max_episode_steps = 13

        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True)
        env_id = textworld.gym.register_games([self.gamefile1, self.gamefile1_z8, self.gamefile2, self.gamefile2],
                                              request_infos=env_options,
                                              batch_size=batch_size,
                                              max_episode_steps=max_episode_steps,
                                              name="test-auto-reset",
                                              asynchronous=True,
                                              auto_reset=True)
        env = textworld.gym.make(env_id)

        init_obs, init_infos = env.reset()
        dones = [False] * batch_size
        for cmd in self.game1.metadata["walkthrough"]:
            assert sum(dones) == 0
            obs, scores, dones, infos = env.step([cmd] * batch_size)

        # Two of the envs should be done.
        assert sum(dones) == 2
        assert sum(scores) == 2

        # The two envs should auto-reset on the next action.
        obs, scores, dones, infos = env.step(["wait"] * batch_size)
        assert sum(dones) == 0
        assert sum(scores) == 0  # Score should auto reset.
        assert obs[0] == init_obs[0] and obs[1] == init_obs[1]
        assert all(v[0] == init_infos[k][0] and v[1] == init_infos[k][1] for k, v in infos.items())

        for cmd in self.game1.metadata["walkthrough"]:
            assert sum(dones) == 0
            obs, scores, dones, infos = env.step([cmd] * batch_size)

        assert sum(dones) == 2

        obs, infos = env.reset()
        for _ in range(max_episode_steps):
            obs, scores, dones, infos = env.step(["wait"] * batch_size)

        assert sum(dones) == 4  # All env have played maximum number of steps.
        env.close()

    def test_make_env(self):
        batch_size = 5
        env_options = EnvInfos(inventory=True, description=True,
                               admissible_commands=True,
                               extras=["walkthrough"])
        env_id = textworld.gym.register_games([self.gamefile1, self.gamefile1_z8],
                                              request_infos=env_options,
                                              batch_size=batch_size,
                                              name="test-fileleak",
                                              asynchronous=True)

        for _ in range(3):
            env = textworld.gym.make(env_id)

            obs, infos = env.reset()
            assert len(obs) == batch_size
            assert len(set(obs)) == 1  # All the same game.
            assert len(infos) == len(env_options)
            for values in infos.values():
                assert len(values) == batch_size

            for cmds in zip(*infos.get("extra.walkthrough")):
                obs, scores, dones, infos = env.step(cmds)

            assert all(dones)
            assert all(score == 1 for score in scores)

    def test_registering_game_with_custom_wrapper(self):

        class DummyWrapper(textworld.core.Wrapper):

            def step(self, command):
                state, score, done = super().step(command)
                state.feedback = "DUMMY: " + state.feedback
                state.inventory = "DUMMY: " + state.inventory
                return state, score, done

        env_options = EnvInfos(inventory=True, extras=["walkthrough"])

        env_id = textworld.gym.register_game(
            self.gamefile1,
            env_options,
            name="test-custom-wrapper",
            wrappers=[DummyWrapper]
        )
        env = textworld.gym.make(env_id)
        obs, infos = env.reset()

        for cmd in infos.get("extra.walkthrough"):
            obs, _, _, infos = env.step(cmd)

            # Check that the wrapper was applied when calling env.step.
            assert obs.startswith("DUMMY: ")
            assert infos["inventory"].startswith("DUMMY: ")

        env.close()
