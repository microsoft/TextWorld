# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
from os.path import join as pjoin
from typing import Optional, Mapping, Tuple

from textworld.utils import g_rng

from textworld.core import Environment, GameState, Agent
from textworld.generator import Game, GameMaker, GameOptions

from textworld.envs import FrotzEnvironment
from textworld.envs import GlulxEnvironment
from textworld.envs import JerichoEnvironment
from textworld.envs import CUSTOM_ENVIRONMENTS

from textworld.agents import HumanAgent

from textworld.generator import make_game, compile_game

# TODO: move that constant in a config file.
DEFAULT_GAMES_REPOSITORY = pjoin(".", "games")


def start(filename: str) -> Environment:
    """ Starts a TextWorld environment to play a game.

    Args:
        filename: Path to the game file.

    Returns:
        TextWorld environment running the provided game.

    """
    # Check the game file exists.
    if not os.path.isfile(filename):
        # Maybe it refers to a file in "games" directory.
        tentative = pjoin(DEFAULT_GAMES_REPOSITORY, filename)

        if not os.path.isfile(tentative):
            msg = "Unable to find game: '{}' or '{}'"
            msg = msg.format(os.path.abspath(filename), os.path.abspath(tentative))
            raise IOError(msg)

        filename = tentative

    # Guess the backend from the extension.
    backend = "glulx" if filename.endswith(".ulx") else "zmachine"

    if backend == "zmachine":
        if os.path.basename(filename) in CUSTOM_ENVIRONMENTS:
            env = CUSTOM_ENVIRONMENTS[os.path.basename(filename)](filename)
        elif JerichoEnvironment:
            env = JerichoEnvironment(filename)
        else:
            env = FrotzEnvironment(filename)

    elif backend == "glulx":
        env = GlulxEnvironment(filename)
    else:
        msg = "Unsupported backend: {}".format(backend)
        raise ValueError(msg)

    return env


def play(game_file: str, agent: Optional[Agent] = None, max_nb_steps: int = 1000,
         wrapper: Optional[callable] = None, silent: bool = False) -> None:
    """ Convenience function to play a text-based game.

    Args:
        game_file: Path to the game file.
        agent: Agent that will play the game. Default: HumanAgent(autocompletion=True).
        max_nb_steps: Maximum number of steps allowed. Default: 1000.
        wrapper: Wrapper to apply to the environment.
        silent: Do not render anything to screen.

    Notes:
        Use script :command:`tw-play` for more options.
    """
    env = start(game_file)
    if agent is None:
        try:
            agent = HumanAgent(autocompletion=True)
        except AttributeError:
            agent = HumanAgent()

    agent.reset(env)
    if wrapper is not None:
        env = wrapper(env)

    game_state = env.reset()
    if not silent:
        env.render(mode="human")

    reward = 0
    done = False
    try:
        for _ in range(max_nb_steps):
            command = agent.act(game_state, reward, done)
            game_state, reward, done = env.step(command)

            if not silent:
                env.render(mode="human")

            if done:
                break

    except KeyboardInterrupt:
        pass  # Stop the game.
    finally:
        env.close()

    if not silent:
        msg = "Done after {} steps. Score {}/{}."
        msg = msg.format(game_state.nb_moves, game_state.score, game_state.max_score)
        print(msg)


def make(options: GameOptions, path: str) -> Tuple[str, Game]:
    """ Makes a text-based game.

    Arguments:
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).
        path: Path of the compiled game (.ulx or .z8). Also, the source (.ni)
              and metadata (.json) files will be saved along with it.

    Returns:
        A tuple containing the path to the game file, and its corresponding Game's object.
    """
    game = make_game(options)
    game_file = compile_game(game, path, force_recompile=True)
    return game_file, game
