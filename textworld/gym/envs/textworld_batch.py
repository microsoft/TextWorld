# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import sys
import textwrap
from io import StringIO
from typing import List, Optional, Dict, Any, Tuple, Union

import numpy as np
import gym
from gym.utils import colorize

from textworld import EnvInfos
from textworld.envs.wrappers import Filter, GenericEnvironment, Limit
from textworld.envs.batch import AsyncBatchEnv, SyncBatchEnv

from textworld.gym.envs.utils import shuffled_cycle

from functools import partial


def _make_env(request_infos, max_episode_steps=None):
    env = GenericEnvironment(request_infos)
    if max_episode_steps:
        env = Limit(env, max_episode_steps=max_episode_steps)

    env = Filter(env)
    return env


class TextworldBatchGymEnv(gym.Env):
    metadata = {'render.modes': ['human', 'ansi', 'text']}

    def __init__(self,
                 gamefiles: List[str],
                 request_infos: Optional[EnvInfos] = None,
                 batch_size: int = 1,
                 asynchronous: bool = True,
                 auto_reset: bool = False,
                 max_episode_steps: Optional[int] = None,
                 action_space: Optional[gym.Space] = None,
                 observation_space: Optional[gym.Space] = None) -> None:
        """ Environment for playing text-based games in batch.

        Arguments:
            gamefiles:
                Paths of every game composing the pool (`*.ulx|*.z[1-8]`).
            request_infos:
                For customizing the information returned by this environment
                (see
                :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
                for the list of available information).

                .. warning:: Only supported for TextWorld games (i.e., that have a corresponding `*.json` file).
            batch_size:
                If provided, it indicates the number of games to play at the same time.
                By default, a single game is played at once.

                .. warning:: When `batch_size` is provided (even for batch_size=1), `env.step` expects
                            a list of commands as input and outputs a list of states. `env.reset` also
                            outputs a list of states.
            asynchronous:
                If `True`, wraps the environments in an `AsyncBatchEnv` (which uses
                `multiprocessing` to run the environments in parallel). If `False`,
                wraps the environments in a `SyncBatchEnv`. Default: `True`.
            auto_reset:
                If `True`, each game *independently* resets once it is done (i.e., reset happens
                on the next `env.step` call).
                Otherwise, once a game is done, subsequent calls to `env.step` won't have any effects.
            max_episode_steps:
                Number of steps allocated to play each game. Once exhausted, the game is done.
            action_space:
                The action space be used with OpenAI baselines.
                (see :py:class:`textworld.gym.spaces.Word <textworld.gym.spaces.text_spaces.Word>`).
            observation_space:
                The observation space be used with OpenAI baselines
                (see :py:class:`textworld.gym.spaces.Word <textworld.gym.spaces.text_spaces.Word>`).
        """
        self.gamefiles = gamefiles
        self.batch_size = batch_size
        self.request_infos = request_infos or EnvInfos()
        self.seed(1234)

        env_fns = [partial(_make_env, self.request_infos, max_episode_steps) for _ in range(self.batch_size)]
        BatchEnvType = AsyncBatchEnv if self.batch_size > 1 and asynchronous else SyncBatchEnv
        self.batch_env = BatchEnvType(env_fns, auto_reset)

        self.action_space = action_space
        self.observation_space = observation_space

    def seed(self, seed: Optional[int] = None) -> List[int]:
        """ Set the seed for this environment's random generator(s).

        This environment use a random generator to shuffle the order in which
        the games are played.

        Arguments:
            seed: Number that will be used to seed the random generators.

        Returns:
            All the seeds used to set this environment's random generator(s).
        """
        # We shuffle the order in which the game will be seen.
        rng = np.random.RandomState(seed)
        gamefiles = list(self.gamefiles)  # Soft copy to avoid shuffling original list.
        rng.shuffle(gamefiles)

        # Prepare iterator used for looping through the games.
        self._gamefiles_iterator = shuffled_cycle(gamefiles, rng=rng)
        return [seed]

    def reset(self) -> Tuple[List[str], Dict[str, List[Any]]]:
        """ Resets the text-based environment.

        Resetting this environment means starting the next game in the pool.

        Returns:
            A tuple (observations, infos) where

            * observation: text observed in the initial state for each game in the batch;
            * infos: additional information as requested for each game in the batch.
        """
        if self.batch_env is not None:
            self.batch_env.close()

        gamefiles = [next(self._gamefiles_iterator) for _ in range(self.batch_size)]
        self.batch_env.load(gamefiles)

        self.last_commands = [None] * self.batch_size
        self.ob, infos = self.batch_env.reset()
        return self.ob, infos

    def skip(self, nb_games: int = 1) -> None:
        """ Skip games.

        Arguments:
            nb_games: Number of games to skip.
        """
        for _ in range(nb_games):
            next(self._gamefiles_iterator)

    def step(self, commands) -> Tuple[List[str], List[float], List[bool], Dict[str, List[Any]]]:
        """ Runs a command in each text-based environment of the batch.

        Arguments:
            commands: Text command to send to the game interpreter.

        Returns:
            A tuple (observations, scores, dones, infos) where

            * observations: text observed in the new state for each game in the batch;
            * scores: total number of points accumulated so far for each game in the batch;
            * dones: whether each game in the batch is finished or not;
            * infos: additional information as requested for each game in the batch.
        """
        self.last_commands = commands
        self.obs, scores, dones, infos = self.batch_env.step(self.last_commands)
        return self.obs, scores, dones, infos

    def close(self) -> None:
        """ Close this environment. """

        if self.batch_env is not None:
            self.batch_env.close()

        self.batch_env = None

    def render(self, mode: str = 'human') -> Optional[Union[StringIO, str]]:
        """ Renders the current state of each environment in the batch.

        Each rendering is composed of the previous text command (if there's one) and
        the text describing the current observation.

        Arguments:
            mode:
                Controls where and how the text is rendered. Supported modes are:

                    * human: Display text to the current display or terminal and
                      return nothing.
                    * ansi: Return a `StringIO` containing a terminal-style
                      text representation. The text can include newlines and ANSI
                      escape sequences (e.g. for colors).
                    * text: Return a string (`str`) containing the text without
                      any ANSI escape sequences.

        Returns:
            Depending on the `mode`, this method returns either nothing, a
            string, or a `StringIO` object.
        """
        outfile = StringIO() if mode in ['ansi', "text"] else sys.stdout

        renderings = []
        for last_command, ob in zip(self.last_commands, self.obs):
            msg = ob.rstrip() + "\n"
            if last_command is not None:
                command = "> " + last_command
                if mode in ["ansi", "human"]:
                    command = colorize(command, "yellow", highlight=False)

                msg = command + "\n" + msg

            if mode == "human":
                # Wrap each paragraph at 80 characters.
                paragraphs = msg.split("\n")
                paragraphs = ["\n".join(textwrap.wrap(paragraph, width=80)) for paragraph in paragraphs]
                msg = "\n".join(paragraphs)

            renderings.append(msg)

        outfile.write("\n-----\n".join(renderings) + "\n")

        if mode == "text":
            outfile.seek(0)
            return outfile.read()

        if mode == 'ansi':
            return outfile
