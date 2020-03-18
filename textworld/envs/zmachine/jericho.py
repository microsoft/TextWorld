# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import warnings

import jericho

import textworld
from textworld.core import GameState
from textworld.core import GameNotRunningError


class JerichoUnsupportedGameWarning(UserWarning):
    pass


class JerichoEnv(textworld.Environment):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seed = -1
        self._jericho = None

    def load(self, z_file: str) -> None:
        self.close()
        self.gamefile = os.path.abspath(z_file)
        _, ext = os.path.splitext(os.path.basename(self.gamefile))

        # Check if game is supported by Jericho.
        if not ext.startswith(".z"):
            raise ValueError("Only .z[1-8] files are supported!")

        if not os.path.isfile(self.gamefile):
            raise FileNotFoundError(self.gamefile)

    def __del__(self) -> None:
        self.close()

    @property
    def game_running(self) -> bool:
        """ Determines if the game is still running. """
        return self._jericho is not None

    def seed(self, seed=None):
        self._seed = seed
        return self._seed

    def _gather_infos(self):
        """ Adds additional information to the internal state. """
        self.state.feedback = self.state.raw
        if not self._jericho.is_fully_supported:
            return  # No more information can be gathered.

        for attr in self.infos.basics:
            self.state[attr] = getattr(self._jericho, "get_" + attr, lambda: self.state.get(attr))()

        for attr in self.infos.extras:
            self.state["extra.{}".format(attr)] = getattr(self._jericho, "get_" + attr, lambda: None)()

        # Deal with information that has different method name in Jericho.
        self.state["won"] = self._jericho.victory()
        self.state["lost"] = self._jericho.game_over()
        self.state["score"] = self._jericho.get_score()
        self.state["location"] = self._jericho.get_player_location()

    def reset(self):
        self.close()  # In case, it is running.

        # Start the game using Jericho.
        self._jericho = jericho.FrotzEnv(self.gamefile, self._seed)

        self.state = GameState()
        self.state.raw, _ = self._jericho.reset()
        self._gather_infos()
        return self.state

    def _send(self, command: str) -> str:
        """ Send a command directly to the interpreter.

        This method will not affect the internal state variable.
        """
        feedback, _, _, _ = self._jericho.step(command)
        return feedback

    def step(self, command):
        if not self.game_running:
            raise GameNotRunningError()

        self.state = GameState()
        self.state.last_command = command.strip()
        res = self._jericho.step(self.state.last_command)
        # As of Jericho >= 2.1.0, the reward is returned instead of the score.
        self.state.raw, _, self.state.done, _ = res
        self._gather_infos()
        return self.state, self.state.score, self.state.done

    def close(self):
        if self.game_running:
            self._jericho.close()
            self._jericho = None


# By default disable the warning about unsupported games.
warnings.simplefilter("ignore", JerichoUnsupportedGameWarning)
