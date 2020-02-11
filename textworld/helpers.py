# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import re
from typing import Optional, Tuple, List

from textworld.core import EnvInfos, Environment, Agent
from textworld.generator.game import Game, GameOptions

from textworld.envs import GitGlulxEnv
from textworld.envs import JerichoEnv
from textworld.envs import TWInform7

from textworld.agents import HumanAgent

from textworld.generator import make_game, compile_game


def start(path: str, infos: Optional[EnvInfos] = None,
          wrappers: List[callable] = []) -> Environment:
    """ Starts a TextWorld environment to play a game.

    Arguments:
        path: Path to the game file.
        infos:
            For customizing the information returned by this environment
            (see
            :py:class:`textworld.EnvInfos <textworld.core.EnvInfos>`
            for the list of available information).
        wrappers: List of wrappers to apply to the environment.

    Returns:
        TextWorld environment running the provided game.

    """
    # Check the game file exists.
    if not os.path.isfile(path):
        msg = "Unable to find game '{}'.".format(os.path.abspath(path))
        raise IOError(msg)

    # Guess the backend from the extension.
    if path.endswith(".ulx"):
        env = GitGlulxEnv(infos)
    elif re.search(r"\.z[1-8]", path):
        env = JerichoEnv(infos)
    else:
        msg = "Unsupported game format: {}".format(path)
        raise ValueError(msg)

    if TWInform7.compatible(path):
        wrappers = [TWInform7] + list(wrappers)

    # Apply all wrappers
    for wrapper in wrappers:
        env = wrapper(env)

    env.load(path)
    return env


def play(game_file: str, agent: Optional[Agent] = None, max_nb_steps: int = 1000,
         wrappers: List[callable] = [], silent: bool = False) -> None:
    """ Convenience function to play a text-based game.

    Args:
        game_file: Path to the game file.
        agent: Agent that will play the game. Default: HumanAgent(autocompletion=True).
        max_nb_steps: Maximum number of steps allowed. Default: 1000.
        wrappers: List of wrappers to apply to the environment.
        silent: Do not render anything to screen.

    Notes:
        Use script :command:`tw-play` for more options.
    """
    agent = agent or HumanAgent()
    env = start(game_file, wrappers=wrappers + agent.wrappers)
    agent.reset(env)
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
        msg = msg.format(game_state.moves, game_state.score, game_state.max_score)
        print(msg)


def make(options: GameOptions) -> Tuple[str, Game]:
    """ Makes a text-based game.

    Arguments:
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        A tuple containing the path to the game file, and its corresponding Game's object.
    """
    game = make_game(options)
    game_file = compile_game(game, options)
    return game_file, game
