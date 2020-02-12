from functools import partial

try:
    from collections.abc import Iterable
except ImportError:
    Iterable = (tuple, list)

from textworld.envs.batch.batch_env import AsyncBatchEnv
from textworld.envs.batch.batch_env import SyncBatchEnv


__all__ = ['make']


def make(game_files, asynchronous=True, wrappers=None, **kwargs):
    """Create a batch environment from a list of game files.

    Parameters
    ----------
    game_files : Iterable of str
        The list of game files.
    asynchronous : bool (default: `True`)
        If `True`, wraps the environments in an `AsyncVectorEnv` (which uses
        `multiprocessing` to run the environments in parallel). If `False`,
        wraps the environments in a `SyncVectorEnv`.
    wrappers : Callable or Iterable of Callables (default: `None`)
        If not `None`, then apply the wrappers to each internal
        environment during creation.

    Returns
    -------
    env : `textworld.envs.batch.BatchEnv` instance
        The batch environment.
    """
    from textworld import start as start_

    def _make_env(game_file):
        env = start_(game_file, **kwargs)
        if wrappers is not None:
            if callable(wrappers):
                env = wrappers(env)
            elif isinstance(wrappers, Iterable) and all([callable(w) for w in wrappers]):
                for wrapper in wrappers:
                    env = wrapper(env)
            else:
                raise NotImplementedError
        return env

    env_fns = [partial(_make_env, game_file=game_file) for game_file in game_files]
    return AsyncBatchEnv(env_fns) if asynchronous else SyncBatchEnv(env_fns)
