# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Tuple, Mapping, Any

from textworld.core import Environment, Wrapper


class Limit(Wrapper):
    """
    Environment wrapper to limit the number of steps.

    """

    def __init__(self, env: Environment, max_episode_steps: int):
        super().__init__(env)
        self.max_episode_steps = max_episode_steps
        self.nb_steps = 0

    def reset(self) -> Tuple[str, Mapping[str, Any]]:
        game_state = super().reset()
        self.nb_steps = 0
        return game_state

    def step(self, command: str) -> Tuple[str, Mapping[str, Any]]:
        game_state, score, done = super().step(command)
        self.nb_steps += 1
        done |= self.nb_steps >= self.max_episode_steps
        return game_state, score, done
