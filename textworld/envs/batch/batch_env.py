
import multiprocessing as mp
from typing import Tuple, List, Dict

import numpy as np

from textworld.core import Environment


def _list_of_dicts_to_dict_of_lists(list_: List[Dict]) -> Dict[str, List]:
    # Convert List[Dict] to Dict[List]
    keys = set(key for dict_ in list_ for key in dict_)
    return {key: [dict_.get(key) for dict_ in list_] for key in keys}


def _child(env_fn, parent_pipe, pipe):
    """
    Event loop run by the child processes
    """
    try:
        parent_pipe.close()

        env = env_fn()

        while True:
            command = pipe.recv()
            # command is a tuple like ("call" | "get", "name.of.attr", extra args...)

            obj = env
            attrs = command[1].split(".")
            for attr in attrs[:-1]:
                obj = getattr(obj, attr)

            if command[0] == "call":
                fct = getattr(obj, attrs[-1])
                result = fct(*command[2])
            elif command[0] == "get":
                result = getattr(obj, attrs[-1])
            elif command[0] == "hasattr":
                result = hasattr(obj, attrs[-1])

            pipe.send(result)

    finally:
        env.close()
        pipe.close()


class _ChildEnv:
    """
    Wrapper for an env in a child process.
    """
    def __init__(self, env_fn):
        self._pipe, child_pipe = mp.Pipe()
        self._process = mp.Process(target=_child, args=(env_fn, self._pipe, child_pipe))
        self._process.daemon = True
        self._process.start()
        child_pipe.close()

    def call(self, method, *args):
        self._pipe.send(("call", method, args))

    def get(self, attr):
        self._pipe.send(("get", attr))

    def hasattr(self, attr):
        self._pipe.send(("hasattr", attr))

    def result(self):
        return self._pipe.recv()

    def call_sync(self, *args):
        self.call(*args)
        return self.result()

    def get_sync(self, *args):
        self.get(*args)
        return self.result()

    def hasattr_sync(self, *args):
        self.hasattr(*args)
        return self.result()

    def __del__(self):
        self.call_sync("close")
        self._pipe.close()
        self._process.terminate()
        self._process.join()


class AsyncBatchEnv(Environment):
    """ Environment to run multiple games in parallel asynchronously. """

    def __init__(self, env_fns: List[callable], auto_reset: bool = False):
        """
        Parameters
        ----------
        env_fns : iterable of callable
            Functions that create the environments.
        """
        self.env_fns = env_fns
        self.auto_reset = auto_reset
        self.batch_size = len(self.env_fns)

        self.envs = []
        for env_fn in self.env_fns:
            self.envs.append(_ChildEnv(env_fn))

    def load(self, game_files: List[str]) -> None:
        assert len(game_files) == len(self.envs)
        for env, game_file in zip(self.envs, game_files):
            env.call("load", game_file)

        # Join
        for env in self.envs:
            env.result()

    def seed(self, seed=None):
        # Use a different seed for each env to decorrelate batch examples.
        rng = np.random.RandomState(seed)
        seeds = list(rng.randint(65635, size=self.batch_size))
        for env, seed in zip(self.envs, seeds):
            env.call_sync("seed", seed)

        return seeds

    def reset(self) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Reset all environments of the batch.

        Returns:
            obs: Text observations, i.e. command's feedback.
            infos: Information requested when creating the environments.
        """
        self.last = [None] * self.batch_size
        for env in self.envs:
            env.call("reset")

        results = [env.result() for env in self.envs]
        obs, infos = zip(*results)
        infos = _list_of_dicts_to_dict_of_lists(infos)
        return obs, infos

    def step(self, actions: List[str]) -> Tuple[List[str], int, bool, Dict[str, List[str]]]:
        """
        Perform one action per environment of the batch.

        Returns:
            obs: Text observations, i.e. command's feedback.
            reward: Current game score.
            done: Whether the game is over or not.
            infos: Information requested when creating the environments.
        """
        results = []

        for i, (env, action) in enumerate(zip(self.envs, actions)):
            if self.last[i] is not None and self.last[i][2]:  # Game has ended on the last step.
                obs, reward, done, infos = self.last[i]  # Copy last state over.

                if self.auto_reset:
                    reward, done = 0., False
                    obs, infos = env.call_sync("reset")

                results.append((obs, reward, done, infos))

            else:
                env.call("step", action)
                results.append(None)

        results = [result or env.result() for env, result in zip(self.envs, results)]
        obs, rewards, dones, infos = zip(*results)
        self.last = results
        infos = _list_of_dicts_to_dict_of_lists(infos)
        return obs, rewards, dones, infos

    def render(self, mode='human'):
        for env in self.envs:
            env.call("render", mode)

        return [env.result() for env in self.envs]

    def close(self):
        for env in self.envs:
            env.call("close")

        # Join
        for env in self.envs:
            env.result()


class SyncBatchEnv(Environment):
    """ Environment to run multiple games independently synchronously. """

    def __init__(self, env_fns: List[callable], auto_reset: bool = False):
        """
        Parameters
        ----------
        env_fns : iterable of callable
            Functions that create the environments
        """
        self.env_fns = env_fns
        self.batch_size = len(self.env_fns)
        self.auto_reset = auto_reset
        self.envs = [env_fn() for env_fn in self.env_fns]

    def load(self, game_files: List[str]) -> None:
        assert len(game_files) == len(self.envs)
        for env, game_file in zip(self.envs, game_files):
            env.load(game_file)

    def seed(self, seed=None):
        # Use a different seed for each env to decorrelate batch examples.
        rng = np.random.RandomState(seed)
        seeds = list(rng.randint(65635, size=self.batch_size))
        for env, seed in zip(self.envs, seeds):
            env.seed(seed)

        return seeds

    def reset(self):
        """
        Reset all environments of the batch.

        Returns:
            obs: Text observations, i.e. command's feedback.
            infos: Information requested when creating the environments.
        """
        self.last = [None] * self.batch_size
        results = [env.reset() for env in self.envs]
        obs, infos = zip(*results)
        infos = _list_of_dicts_to_dict_of_lists(infos)
        return obs, infos

    def step(self, actions):
        """
        Perform one action per environment of the batch.

        Returns:
            obs: Text observations, i.e. command's feedback.
            reward: Current game score.
            done: Whether the game is over or not.
            infos: Information requested when creating the environments.
        """
        results = []
        for i, (env, action) in enumerate(zip(self.envs, actions)):
            if self.last[i] is not None and self.last[i][2]:  # Game has ended on the last step.
                obs, reward, done, infos = self.last[i]  # Copy last state over.

                if self.auto_reset:
                    reward, done = 0., False
                    obs, infos = env.reset()

                results.append((obs, reward, done, infos))
            else:
                results.append(env.step(action))

        self.last = results

        obs, rewards, dones, infos = zip(*results)
        infos = _list_of_dicts_to_dict_of_lists(infos)
        return obs, rewards, dones, infos

    def render(self, mode='human'):
        return [env.render(mode=mode) for env in self.envs]

    def close(self):
        for env in self.envs:
            env.close()
