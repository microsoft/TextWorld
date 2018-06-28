# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import os
import sys

import jericho

import textworld
from textworld.core import GameState


class DefaultZGameState(GameState):

    @property
    def nb_deaths(self):
        """ Number of times the player has died. """
        return -1

    @property
    def feedback(self):
        """ Interpreter's response after issuing last command. """
        if not hasattr(self, "_feedback"):
            # Extract feeback from command's output.
            self._feedback = self._raw

        return self._feedback

    @property
    def inventory(self):
        """ Player's inventory. """
        if not hasattr(self, "_inventory"):
            # Issue the "inventory" command and parse its output.
            self._inventory, _, _ = self._env.step("inventory")

        return self._inventory

    @property
    def score(self):
        """ Current score. """
        if not hasattr(self, "_score"):
            self._score = 0

        return self._score

    @property
    def max_score(self):
        """ Max score for this game. """
        if not hasattr(self, "_max_score"):
            self._score = 0

        return self._max_score

    @property
    def description(self):
        """ Description of the current location. """
        if not hasattr(self, "_description"):
            # Issue the "look" command and parse its output.
            self._description, _, _ = self._env.step("look")

        return self._description

    @property
    def has_won(self):
        """ Whether the player has won the game or not. """
        return False

    @property
    def has_lost(self):
        """ Whether the player has lost the game or not. """
        return False


class JerichoEnvironment(textworld.Environment):
    GAME_STATE_CLASS = DefaultZGameState

    metadata = {'render.modes': ['human', 'ansi', 'text']}

    def __init__(self, game_filename):
        """
        Parameters
        ----------
        game_filename : str
            The game's filename.
        """
        self._seed = -1
        self._jericho = None
        self.game_filename = os.path.abspath(game_filename)
        self.game_name, ext = os.path.splitext(os.path.basename(game_filename))

        # Check if game is supported by Jericho.
        if not ext.startswith(".z"):
            raise ValueError("Only .z[1-8] files are supported!")

        if not os.path.isfile(self.game_filename):
            raise FileNotFoundError(game_filename)

        if not jericho.FrotzEnv.is_fully_supported(self.game_filename):
            raise ValueError("Game is not fully supported by Jericho: {}".format(game_filename))

    def seed(self, seed=None):
        self._seed = seed
        return self._seed

    def reset(self):
        self.close()  # In case, it is running.
        self.game_state = self.GAME_STATE_CLASS(self)

        # Start the game using Jericho.
        self._jericho = jericho.FrotzEnv(self.game_filename, self._seed)

        # Grab start info from game.
        start_output = self._jericho.reset()
        self.game_state.init(start_output)
        self.game_state._score = self._jericho.get_score()
        self.game_state._max_score = self._jericho.get_max_score()
        return self.game_state

    def step(self, command):
        command = command.strip()
        output, reward, done, _ = self._jericho.step(command)
        self.game_state = self.game_state.update(command, output)
        self.game_state._score = self._jericho.get_score()
        self.game_state._max_score = self._jericho.get_max_score()
        return self.game_state, reward, done

    def close(self):
        if self._jericho is not None:
            self._jericho.close()
            self._jericho = None

    def render(self, mode='human', close=False):
        if close:
            return

        outfile = io.StringIO() if mode in ['ansi', "text"] else sys.stdout

        if self.display_command_during_render and self.game_state.command is not None:
            command = "> " + self.game_state.command
            outfile.write(command + "\n\n")

        observation = self.game_state.feedback
        outfile.write(observation + "\n")

        if mode == "text":
            outfile.seek(0)
            return outfile.read()

        if mode == 'ansi':
            return outfile
