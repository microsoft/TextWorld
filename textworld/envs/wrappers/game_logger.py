import sys
from typing import Tuple, List

from textworld.core import Environment, GameState, Wrapper


class GameLogger(Wrapper):
    def __init__(self, env: Environment) -> None:
        """
        Wrap around a TextWorld environment to provide logging capabilities.

        Parameters
        ----------
        :param env:
            The TextWorld environment to wrap. Has the correct knowledge base.
        """
        super().__init__(env)
        self.activate_state_tracking()

        self.serialized_game = env

        self.logs = []
        self.current_log = {}

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        if self.current_log:
            self.logs.append(self.current_log)
            self.current_log = {}

        self.current_log['action_taken'] = command

        game_state, score, done = super().step(command)
        return game_state, score, done

    def log_action_distribution(self, actions: List, probabilities: List):
        action_dist = {a: p for a, p in zip(actions, probabilities)}
        self.current_log['action_distribution'] = action_dist

        return self.logs

    def log(self, to_log):
        self.current_log['others'] = to_log

        return self.logs[:].append(self.current_log)
