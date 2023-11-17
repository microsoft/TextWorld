# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import warnings

import jericho

import textworld
from textworld.core import GameState
from textworld.core import GameNotRunningError


class JerichoEnv(textworld.Environment):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seed = -1
        self._jericho = None
        self.gamefile = None
        self._reset = False

    def load(self, z_file: str) -> None:
        self.gamefile = os.path.abspath(z_file)
        _, ext = os.path.splitext(os.path.basename(self.gamefile))

        # Check if game is supported by Jericho.
        if not ext.startswith(".z"):
            raise ValueError("Only .z[1-8] files are supported!")

        if not os.path.isfile(self.gamefile):
            raise FileNotFoundError(self.gamefile)

        if self._jericho is None:
            # Start the game using Jericho.
            self._jericho = jericho.FrotzEnv(self.gamefile, self._seed)
        else:
            self._jericho.load(self.gamefile)

    def __del__(self) -> None:
        self.close()

    @property
    def game_running(self) -> bool:
        """ Determines if the game is still running. """
        return self._jericho is not None

    def seed(self, seed=None):
        self._seed = seed
        if self._jericho:
            self._jericho.seed(self._seed)

        return self._seed

    def _gather_infos(self):
        """ Adds additional information to the internal state. """
        self.state.feedback = self.state.raw
        if not self._jericho.is_fully_supported:
            return  # No more information can be gathered.

        for attr in self.request_infos.basics:
            self.state[attr] = getattr(self._jericho, "get_" + attr, lambda: self.state.get(attr))()

        for attr in self.request_infos.extras:
            self.state["extra.{}".format(attr)] = getattr(self._jericho, "get_" + attr, lambda: None)()

        # Deal with information that has different method name in Jericho.
        self.state["won"] = self._jericho.victory()
        self.state["lost"] = self._jericho.game_over()
        self.state["score"] = self._jericho.get_score()
        self.state["moves"] = self._jericho.get_moves()
        self.state["location"] = self._jericho.get_player_location()

        if self.request_infos.description:
            bkp = self._jericho.get_state()
            self.state["description"], _, _, _ = self._jericho.step("look")
            self._jericho.set_state(bkp)

        if self.request_infos.inventory:
            bkp = self._jericho.get_state()
            self.state["inventory"], _, _, _ = self._jericho.step("inventory")
            self._jericho.set_state(bkp)

        if self.request_infos.admissible_commands:
            self.state["_valid_commands"] = self._jericho.get_valid_actions()
            self.state["admissible_commands"] = sorted(set(self.state["_valid_commands"]))

    def reset(self):
        if not self.game_running:
            raise GameNotRunningError("Call env.load(gamefile) before env.reset().")

        self.state = GameState()
        self.state.raw, _ = self._jericho.reset()
        self._gather_infos()
        self._reset = True
        return self.state

    def _send(self, command: str) -> str:
        """ Send a command directly to the interpreter.

        This method will not affect the internal state variable.
        """
        feedback, _, _, _ = self._jericho.step(command)
        return feedback

    def step(self, command):
        if not self.game_running or not self._reset:
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
            self._reset = False

    def copy(self) -> "JerichoEnv":
        """ Return a copy of this environment at the same state. """
        env = JerichoEnv(self.request_infos)
        env._seed = self._seed

        if self.gamefile:
            env.load(self.gamefile)

        if self._jericho:
            env._jericho = self._jericho.copy()
            env._reset = True

        # Copy core Environment's attributes.
        env.state = self.state.copy()
        env.request_infos = self.request_infos.copy()
        return env


# By default disable the warning about unsupported games.
warnings.simplefilter("ignore", jericho.UnsupportedGameWarning)
