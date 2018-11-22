import re
import os
import sys
from glob import glob
from io import StringIO
from os.path import join as pjoin
from typing import List, Optional, Iterable

import numpy as np
import gym
from gym.utils import colorize

import textworld
import textworld.text_utils

from textworld.gym.spaces import text_spaces
from textworld.gym.utils import make_looping_shuffled_iterator


class TextworldGameEnv(gym.Env):
    metadata = {'render.modes': ['human', 'ansi']}

    def __init__(self, game_file: str, request_infos: List[str] = [],
                 action_space: Optional[gym.Space] = None,
                 observation_space: Optional[gym.Space] = None):
        """
        Environment for a single TextWorld game.

        Arguments:
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
                 * `'extras:<name>'`: extras information unique to some games;
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
        self.game_file = game_file
        self.request_infos = request_infos

        self.game = textworld.Game.load(os.path.splitext(self.game_file)[0] + ".json")
        self.textworld_env = textworld.start(self.game_file)

        if action_space is None or observation_space is None:
            # Extract vocabulary from game.
            vocab = textworld.text_utils.extract_vocab([self.game])

        self.action_space = action_space or text_spaces.Word(max_length=8, vocab=vocab)
        self.observation_space = observation_space or text_spaces.Word(max_length=200, vocab=vocab)

        self.last_command = None
        self.infos = None

        if "admissible_commands" in self.request_infos:
            self.textworld_env.activate_state_tracking()

        if "intermediate_reward" in self.request_infos:
            self.textworld_env.activate_state_tracking()
            self.textworld_env.compute_intermediate_reward()

    def seed(self, seed=None):
        return [seed]

    def reset(self):
        self.infos = {}
        self.game_state = self.textworld_env.reset()
        ob = self.game_state.feedback
        self._update_requested_infos()
        return ob, self.infos

    def _update_requested_infos(self):
        # Make sure requested infos are available.
        for attr in self.request_infos:
            # The following will take care of retrieving the information
            # from the game interpreter if needed.
            if attr.startswith("extra:"):
                self.infos[attr] = self.game_state.extras.get(attr.split(":")[-1])
            else:
                self.infos[attr] = getattr(self.game_state, attr)

    def step(self, action):
        self.last_command = action
        self.game_state, reward, done = self.textworld_env.step(self.last_command)
        ob = self.game_state.feedback
        self._update_requested_infos()
        return ob, reward, done, self.infos

    def render(self, mode='human'):
        outfile = StringIO() if mode == 'ansi' else sys.stdout

        if self.last_command is not None:
            command = colorize("> " + self.last_command, "yellow", highlight=False)
            outfile.write(command + "\n\n")

        outfile.write(self.game_state.feedback + "\n")

        if mode != 'human':
            return outfile

    def close(self):
        if self.textworld_env is not None:
            self.textworld_env.close()

        self.textworld_env = None


class TextworldGamesEnv(gym.Env):
    metadata = {'render.modes': ['human', 'ansi']}

    def __init__(self, game_files: List[str], request_infos: List[str] = [],
                 action_space: Optional[gym.Space] = None,
                 observation_space: Optional[gym.Space] = None):
        """
        Environment for a pool of TextWorld games.

        Each time `TextworldGamesEnv.reset()` is called, a new game from the
        pool starts. Each game is guaranteed to be played once before a
        same game is played for a second time.

        Arguments:
            game_files:
                Paths of every TextWorld game composing the pool (.ulx + .json).
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
                 * `'extras:<name>'`: extras information unique to some games;
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
        self.seed(1234)
        self.request_infos = request_infos
        self.current_game = None
        self.textworld_env = None

        if action_space is None or observation_space is None:
            # Extract vocabulary from games.
            games_iter = (textworld.Game.load(os.path.splitext(gamefile)[0] + ".json") for gamefile in self.gamefiles)
            vocab = textworld.text_utils.extract_vocab(games_iter)

        self.action_space = action_space or text_spaces.Word(max_length=8, vocab=vocab)
        self.observation_space = observation_space or text_spaces.Word(max_length=200, vocab=vocab)

        self.last_command = None
        self.infos = None

    def seed(self, seed=None):
        self.rng_games = np.random.RandomState(1234)  # To shuffle games between epochs.

        # We shuffle the order in which the game will be seen.
        rng = np.random.RandomState(seed)
        rng.shuffle(self.gamefiles)

        # Prepare iterator used for looping through the games.
        self._gamefiles_iterator = make_looping_shuffled_iterator(self.gamefiles,
                                                                  rng=self.rng_games)

        return [seed]

    def reset(self):
        self.current_game = next(self._gamefiles_iterator)
        self.infos = {}

        if self.textworld_env is not None:
            self.textworld_env.close()

        self.textworld_env = textworld.start(self.current_game)

        if "admissible_commands" in self.request_infos:
            self.textworld_env.activate_state_tracking()

        if "intermediate_reward" in self.request_infos:
            self.textworld_env.activate_state_tracking()
            self.textworld_env.compute_intermediate_reward()

        self.game_state = self.textworld_env.reset()
        ob = self.game_state.feedback
        self._update_requested_infos()
        return ob, self.infos

    def _update_requested_infos(self):
        # Make sure requested infos are available.
        for attr in self.request_infos:
            # The following will take care of retrieving the information
            # from the game interpreter if needed.
            if attr.startswith("extra:"):
                self.infos[attr] = self.game_state.extras.get(attr.split(":")[-1])
            else:
                self.infos[attr] = getattr(self.game_state, attr)

    def skip(self, ngames=1):
        for i in range(ngames):
            next(self._gamefiles_iterator)

    def step(self, action):
        self.last_command = action
        self.game_state, reward, done = self.textworld_env.step(self.last_command)
        ob = self.game_state.feedback
        self._update_requested_infos()
        return ob, reward, done, self.infos

    def render(self, mode='human'):
        outfile = StringIO() if mode == 'ansi' else sys.stdout

        if self.last_command is not None:
            command = colorize("> " + self.last_command, "yellow", highlight=False)
            outfile.write(command + "\n\n")

        outfile.write(self.game_state.feedback + "\n")

        if mode != 'human':
            return outfile

    def close(self):
        if self.textworld_env is not None:
            self.textworld_env.close()

        self.textworld_env = None
