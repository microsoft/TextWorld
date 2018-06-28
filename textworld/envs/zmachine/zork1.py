# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re

from textworld import text_utils
from textworld.core import GameState
from textworld.envs import FrotzEnvironment


class Zork1GameState(GameState):

    def _remove_header(self, text):
        cleaned_text = text_utils.remove_header(text)
        return cleaned_text.lstrip("\n")

    def _check_for_death(self, text):
        return "****  You have died  ****" in text

    @property
    def nb_deaths(self):
        """ Number of times the player has died. """
        if not hasattr(self, "_nb_deaths"):
            if self.previous_state is None:
                self._nb_deaths = 0
            else:
                has_died = self._check_for_death(self.feedback)
                self._nb_deaths = self.previous_state.nb_deaths + has_died

        return self._nb_deaths

    @property
    def feedback(self):
        """ Interpreter's response after issuing last command. """
        if not hasattr(self, "_feedback"):
            # Extract feeback from command's output.
            self._feedback = self._remove_header(self._raw)
            if self.previous_state is None:
                # Remove version number and copyright text.
                self._feedback = "\n".join(self._feedback.split("\n")[5:])

        return self._feedback

    @property
    def inventory(self):
        """ Player's inventory. """
        if not hasattr(self, "_inventory"):
            # Issue the "inventory" command and parse its output.
            text = self._env.send("inventory")
            self._inventory = self._remove_header(text)

        return self._inventory

    def _retrieve_score(self):
        if self.has_won or self.has_lost:
            _score_text = self.feedback
        else:
            # Issue the "score" command and parse its output.
            text = self._env.send("score")
            _score_text = self._remove_header(text)

        regex = r"Your score is (?P<score>[0-9]+) \(total of (?P<max_score>[0-9]+) points\)"
        match = re.match(regex, _score_text)
        self._score = int(match.groupdict()['score'].strip())
        self._max_score = int(match.groupdict()['max_score'].strip())
        return self._score, self._max_score

    @property
    def score(self):
        """ Current score. """
        if not hasattr(self, "_score"):
            self._retrieve_score()

        return self._score

    @property
    def max_score(self):
        """ Max score for this game. """
        if not hasattr(self, "_max_score"):
            self._retrieve_score()

        return self._max_score

    @property
    def description(self):
        """ Description of the current location. """
        if not hasattr(self, "_description"):
            # Issue the "look" command and parse its output.
            text = self._env.send("look")
            self._description = self._remove_header(text)

        return self._description

    @property
    def has_won(self):
        """ Whether the player has won the game or not. """
        return "Inside the Barrow" in self.feedback.split("\n")[0]

    @property
    def has_lost(self):
        """ Whether the player has lost the game or not. """
        return self.nb_deaths >= 3


class Zork1Environment(FrotzEnvironment):
    GAME_STATE_CLASS = Zork1GameState
