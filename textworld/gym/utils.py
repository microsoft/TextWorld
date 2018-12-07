from typing import List, Optional

from gym.envs.registration import register, spec, registry

from textworld import EnvInfos


def register_games(game_files: List[str],
                   request_infos: Optional[EnvInfos] = None,
                   max_episode_steps: int = 50,
                   name: str = "") -> str:
    """ Make an environment that will cycle through a list of games.

    Arguments:
        game_files:
            Paths for the TextWorld games (.ulx).
        request_infos:
            For customizing the information returned by this environment
            (see
            :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
            for the list of available information).
        max_episode_steps:
            Terminate a game after that many steps.
        name:
            Name for the new environment, i.e. "tw-{name}-v0". By default,
            the returned env_id is "tw-v0".

    Returns:
        The corresponding gym-compatible env_id to use.

    Example:

        >>> from textworld.generator import make_game, compile_game
        >>> options = textworld.GameOptions()
        >>> options.seeds = 1234
        >>> game = make_game(options)
        >>> game.extras["more"] = "This is extra information."
        >>> game_file = compile_game(game)
        <BLANKLINE>
        >>> import gym
        >>> import textworld.gym
        >>> from textworld import EnvInfos
        >>> request_infos = EnvInfos(description=True, inventory=True, extras=["more"])
        >>> env_id = textworld.gym.register_games([game_file], request_infos)
        >>> env = gym.make(env_id)
        >>> ob, infos = env.reset()
        >>> print(infos["extra.more"])
        This is extra information.

    """
    env_id = "tw-{}-v0".format(name) if name else "tw-v0"

    # If env already registered, bump the version number.
    if env_id in registry.env_specs:
        base, _ = env_id.rsplit("-v", 1)
        versions = [int(env_id.rsplit("-v", 1)[-1]) for env_id in registry.env_specs if env_id.startswith(base)]
        env_id = "{}-v{}".format(base, max(versions) + 1)

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


def register_game(game_file: str,
                  request_infos: Optional[EnvInfos] = None,
                  max_episode_steps: int = 50,
                  name: str = "") -> str:
    """ Make an environment for a particular game.

    Arguments:
        game_file:
            Path for the TextWorld game (.ulx).
        request_infos:
            For customizing the information returned by this environment
            (see
            :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
            for the list of available information).
        max_episode_steps:
            Terminate a game after that many steps.
        name:
            Name for the new environment, i.e. "tw-{name}-v0". By default,
            the returned env_id is "tw-v0".

    Returns:
        The corresponding gym-compatible env_id to use.

    Example:

        >>> from textworld.generator import make_game, compile_game
        >>> options = textworld.GameOptions()
        >>> options.seeds = 1234
        >>> game = make_game(options)
        >>> game.extras["more"] = "This is extra information."
        >>> game_file = compile_game(game)
        <BLANKLINE>
        >>> import gym
        >>> import textworld.gym
        >>> from textworld import EnvInfos
        >>> request_infos = EnvInfos(description=True, inventory=True, extras=["more"])
        >>> env_id = textworld.gym.register_game(game_file, request_infos)
        >>> env = gym.make(env_id)
        >>> ob, infos = env.reset()
        >>> print(infos["extra.more"])
        This is extra information.

    """
    return register_games([game_file], request_infos, max_episode_steps, name)


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
