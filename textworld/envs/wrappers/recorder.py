# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Tuple

from textworld.core import GameState, Wrapper


class Recorder(Wrapper):
    def __init__(self) -> None:
        self.actions = []
        self.last_game_state = None

    def _wrap(self, env):
        super()._wrap(env)
        # Recording requires some additional information.
        self.infos.last_action = True

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        res = super().step(command)
        game_state = res[0]
        self.actions.append(game_state._last_action)
        self.last_game_state = game_state
        return res

    def reset(self) -> GameState:
        self.actions = []
        self.last_game_state = None
        return super().reset()
