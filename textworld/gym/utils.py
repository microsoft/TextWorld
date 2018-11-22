import os
from typing import List, Iterable, Optional

from numpy.random import RandomState

from gym.envs.registration import register, spec


def make_looping_shuffled_iterator(iterable: Iterable, rng: RandomState, nb_loops: int = -1):
    """
    Yield each element of `iterable` one by one, then shuffle the elements
    and start yielding from the start. Stop after `nb_loops` loops.

    Arguments:
        iterable: Iterable containing the elements to yield.
        rng: Random generator used to shuffle the elements after each loop.
        nb_loops: Number of times to go through all the elements. If set to -1,
                  loop an infinite number of times.
    """
    elements = []
    for e in iterable:
        elements.append(e)
        yield e

    cpt = nb_loops
    while cpt != 0:
        cpt -= 1
        rng.shuffle(elements)
        for e in elements:
            yield e


def register_game(name: str, game_file: str, request_infos: List[str] = [],
                  max_episode_steps=50) -> str:
    """ Make an environment that will cycle through a list of games.

    Arguments:
        name: Name that will be part of the returned environment ID.
        game_file:
            Path to a TextWorld game (.ulx + .json).
        request_infos:
            Specify which additional information from the `GameState` object
            should be available in the `infos` dictionary returned by
            `env.reset()` and `env.step()`. Possible choices are:

                * `'description'`: text description of the current room,
                i.e. output of the `look` command;
                * `'inventory'`: text listing of the player's inventory,
                i.e. output of the `inventory` command;
                * `'max_score'`: maximum reachable score of the game;
                * `'objective'`: objective of the game described in text;
                * `'entities'`: names of all entities in the game;
                * `'verbs'`: verbs understood by the the game;
                * `'command_templates'`: templates for commands understood
                by the the game;
                * `'admissible_commands'`: all commands relevant to the
                current state;
                * `'extra:<name>'`: extra information unique to some games;
        max_episode_steps: Terminate a game after that many steps.

    Returns:
        The corresponding gym-compatible env_id to use.

    Example:

        >>> from textworld.generator import make_game, compile_game
        >>> options = textworld.GameOptions()
        >>> options.seeds = 1234
        >>> game = make_game(options)
        >>> game.extras["more"] = "This is extra information."
        >>> game_file = compile_game(game, './tw_games/')
        <BLANKLINE>
        >>> import gym
        >>> import textworld.gym
        >>> request_infos = ["description", "inventory", "extra:more"]
        >>> env_id = textworld.gym.register_game(game_file, request_infos)
        >>> env = gym.make(env_id)
        >>> ob, infos = env.reset()
        >>> print(infos["extra:more"])
        This is extra information.

    """
    env_id = "tw-{}-v0".format(name)

    register(
        id=env_id,
        entry_point='textworld.gym.envs:TextworldGameEnv',
        max_episode_steps=max_episode_steps,
        kwargs={
            'game_file': game_file,
            'request_infos': request_infos,
            }
    )
    return env_id


def register_games(name: str, game_files: List[str], request_infos: List[str] = [],
                   max_episode_steps=50) -> str:
    """ Make an environment that will cycle through a list of games.

    Arguments:
        name: Name that will be part of the returned environment ID.
        game_files:
            Paths to a pool of TextWorld games (.ulx + .json).
        request_infos:
            Specify which additional information from the `GameState` object
            should be available in the `infos` dictionary returned by
            `env.reset()` and `env.step()`. Possible choices are:

                * `'description'`: text description of the current room,
                i.e. output of the `look` command;
                * `'inventory'`: text listing of the player's inventory,
                i.e. output of the `inventory` command;
                * `'max_score'`: maximum reachable score of the game;
                * `'objective'`: objective of the game described in text;
                * `'entities'`: names of all entities in the game;
                * `'verbs'`: verbs understood by the the game;
                * `'command_templates'`: templates for commands understood
                by the the game;
                * `'admissible_commands'`: all commands relevant to the
                current state;
                * `'extra:<name>'`: extra information unique to some games;
        max_episode_steps: Terminate a game after that many steps.

    Returns:
        The corresponding gym-compatible env_id to use.

    Example:

        >>> from textworld.generator import make_game, compile_game
        >>> options = textworld.GameOptions()
        >>> options.seeds = 1234
        >>> game = make_game(options)
        >>> game.extras["more"] = "This is extra information."
        >>> game_file = compile_game(game, './tw_games/')
        <BLANKLINE>
        >>> import gym
        >>> import textworld.gym
        >>> request_infos = ["description", "inventory", "extra:more"]
        >>> env_id = textworld.gym.register_games([game_file], request_infos)
        >>> env = gym.make(env_id)
        >>> ob, infos = env.reset()
        >>> print(infos["extra:more"])
        This is extra information.

    """
    env_id = "tw-{}-v0".format(name)

    register(
        id=env_id,
        entry_point='textworld.gym.envs:TextworldGamesEnv',
        max_episode_steps=max_episode_steps,
        kwargs={
            'game_files': game_files,
            'request_infos': request_infos,
            }
    )
    return env_id


def make_batch(env_id: str, batch_size: int, parallel: bool = False) -> str:
    """ Make an environment that runs multiple games independently.

    Arguments:
        env_id:
            Environment ID that will compose a batch.
        batch_size:
            Number of independent environments to run.
        parallel:
            If True, the environment will be executed in different processes.

    Returns:
        The corresponding gym-compatible env_id to use.
    """
    batch_env_id = "batch{}-".format(batch_size) + env_id
    env_spec = spec(env_id)
    entry_point = 'textworld.gym.envs:BatchEnv'
    if parallel and batch_size > 1:
        entry_point = 'textworld.gym.envs:ParallelBatchEnv'

    register(
        id=batch_env_id,
        entry_point=entry_point,
        max_episode_steps=env_spec.max_episode_steps,
        max_episode_seconds=env_spec.max_episode_seconds,
        nondeterministic=env_spec.nondeterministic,
        reward_threshold=env_spec.reward_threshold,
        trials=env_spec.trials,
        # Setting the 'vnc' tag avoid wrapping the env with a TimeLimit wrapper. See
        # https://github.com/openai/gym/blob/4c460ba6c8959dd8e0a03b13a1ca817da6d4074f/gym/envs/registration.py#L122
        tags={"vnc": "foo"},
        kwargs={'env_id': env_id, 'batch_size': batch_size}
    )

    return batch_env_id
