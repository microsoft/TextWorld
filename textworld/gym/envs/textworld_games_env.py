import re
import os
import sys
import textwrap
from glob import glob
from io import StringIO
from os.path import join as pjoin
from typing import List, Optional, Iterable, Dict, Any, Tuple, Union

import numpy as np
import gym
from gym.utils import colorize

import textworld
import textworld.text_utils
from textworld import EnvInfos
from textworld.envs.wrappers import Filter

from textworld.gym.spaces import text_spaces
from textworld.gym.envs.utils import shuffled_cycle


class TextworldGamesEnv(gym.Env):
    metadata = {'render.modes': ['human', 'ansi', 'text']}

    def __init__(self, game_files: List[str],
                 request_infos: Optional[EnvInfos] = None,
                 action_space: Optional[gym.Space] = None,
                 observation_space: Optional[gym.Space] = None) -> None:
        """ Environment for playing TextWorld games.

        Each time `TextworldGamesEnv.reset()` is called, a new game from the
        pool starts. Each game of the pool is guaranteed to be played exactly
        once before a same game is played for a second time.

        Arguments:
            game_files:
                Paths of every TextWorld game composing the pool (.ulx + .json).
            request_infos:
                For customizing the information returned by this environment
                (see
                :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
                for the list of available information).
            action_space:
                The action space of this TextWorld environment. By default, a
                :py:class:`textworld.gym.spaces.Word <textworld.gym.spaces.text_spaces.Word>`
                instance is used with a `max_length` of 8 and a vocabulary
                extracted from the TextWorld game.
            observation_space:
                The observation space of this TextWorld environment. By default, a
                :py:class:`textworld.gym.spaces.Word <textworld.gym.spaces.text_spaces.Word>`
                instance is used with a `max_length` of 200 and a vocabulary
                extracted from the TextWorld game.
        """
        self.gamefiles = game_files
        self.request_infos = request_infos or EnvInfos()
        self.ob = None
        self.last_command = None
        self.textworld_env = None
        self.current_gamefile = None
        self.seed(1234)

        if action_space is None or observation_space is None:
            # Extract vocabulary from games.
            games_iter = (textworld.Game.load(os.path.splitext(gamefile)[0] + ".json") for gamefile in self.gamefiles)
            vocab = textworld.text_utils.extract_vocab(games_iter)

        self.action_space = action_space or text_spaces.Word(max_length=8, vocab=vocab)
        self.observation_space = observation_space or text_spaces.Word(max_length=200, vocab=vocab)

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

    def reset(self) -> Tuple[str, Dict[str, Any]]:
        """ Resets the text-based environment.

        Resetting this environment means starting the next game in the pool.

        Returns:
            A tuple (observation, info) where

            * observation: text observed in the initial state;
            * infos: additional information as requested.
        """
        if self.textworld_env is not None:
            self.textworld_env.close()

        self.current_gamefile = next(self._gamefiles_iterator)
        env = textworld.start(self.current_gamefile)
        self.textworld_env = Filter(self.request_infos)(env)

        self.ob, infos = self.textworld_env.reset()
        return self.ob, infos

    def skip(self, nb_games: int = 1) -> None:
        """ Skip games.

        Arguments:
            nb_games: Number of games to skip.
        """
        for _ in range(nb_games):
            next(self._gamefiles_iterator)

    def step(self, command) -> Tuple[str, Dict[str, Any]]:
        """ Runs a command in the text-based environment.

        Arguments:
            command: Text command to send to the game interpreter.

        Returns:
            A tuple (observation, score, done, info) where

            * observation: text observed in the new state;
            * score: total number of points accumulated so far;
            * done: whether the game is finished or not;
            * infos: additional information as requested.
        """
        self.last_command = command
        self.ob, score, done, infos = self.textworld_env.step(self.last_command)
        return self.ob, score, done, infos

    def close(self) -> None:
        """ Close this environment. """

        if self.textworld_env is not None:
            self.textworld_env.close()

        self.textworld_env = None

    def render(self, mode: str = 'human') -> Optional[Union[StringIO, str]]:
        """ Renders the current state of this environment.

        The rendering is composed of the previous text command (if there's one) and
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

        msg = self.ob.rstrip() + "\n"
        if self.last_command is not None:
            command = "> " + self.last_command
            if mode in ["ansi", "human"]:
                command = colorize(command, "yellow", highlight=False)

            msg = command + "\n" + msg

        if mode == "human":
            # Wrap each paragraph at 80 characters.
            paragraphs = msg.split("\n")
            paragraphs = ["\n".join(textwrap.wrap(paragraph, width=80)) for paragraph in paragraphs]
            msg = "\n".join(paragraphs)

        outfile.write(msg + "\n")

        if mode == "text":
            outfile.seek(0)
            return outfile.read()

        if mode == 'ansi':
            return outfile
