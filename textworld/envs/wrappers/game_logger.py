import sys
from typing import Tuple

from textworld.core import Environment, GameState, Wrapper


class GameLogger(Wrapper):
    def __init__(self, env: Environment) -> None:
        """
        Wrap around a TextWorld environment to provide logging capabilities.

        Parameters
        ----------
        :param env:
            The TextWorld environment to wrap
        """
        super().__init__(env)
        self.activate_state_tracking()

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        game_state, score, done = super().step(command)
