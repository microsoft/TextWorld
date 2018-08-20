# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from typing import Tuple, List, Optional, Iterable, Union, Sized, Any, Mapping

from textworld.core import Environment, GameState, Wrapper
from textworld.envs.glulx.git_glulx_ml import GitGlulxMLEnvironment, GlulxGameState
from textworld.envs.wrappers import GameLog


class GlulxLogger(Wrapper):
    def __init__(self, env: GitGlulxMLEnvironment) -> None:
        """
        Wrap around a TextWorld GitGlulxML environment to provide logging capabilities.

        Args:
            env: The GitGlulxML environment to wrap.
        """
        super().__init__(env)
        self.activate_state_tracking()

        self.serialized_game = env.game.serialize()
        self._gamefile = env.gamefile

        self._logs = GameLog()
        self._current_log = self._logs.current_game
        self._current_log.append({})
        self._current = self._current_log[-1]


    def step(self, command: str) -> Tuple[GlulxGameState, float, bool]:
        """
        Take a step in the environment.
        Args:
            command: input string for taking an action

        Returns:
            GlulxGameState, score and done.
        """

        self._current['command'] = command

        game_state, score, done = super().step(command)
        self._current['feedback'] = game_state.feedback
        self._current['score'] = score
        self._current['done'] = done
        self._current['action'] = game_state.action.serialize()
        self._current['state'] = game_state.state.serialize()

        return game_state, score, done

    def reset(self) -> GameState:
        """
        Reset the environment.
        Adds a new game into the logs.
        Returns:
            GameState
        """
        # if not self._current
        self._logs = []
        game_state = super().reset()
        self._current = {'optional': []}
        self._current['done'] = False
        self._current['state'] = game_state.state.serialize()

        return game_state

    def add_commands(self, commands: List[str], scores: Optional[Union[Iterable[float], Sized]]=None) -> None:
        """
        Add custom commands to the logger. Optionally add scores for each command.
        Args:
            commands: A list of commands.
            scores: scores for each command. Must be same size as commands if provided.

        Returns:

        """
        if scores is not None:
            self._current['command_scores'] = scores

        self._current['commands'] = commands

    def add(self, info: Any) -> None:
        """
        Add any additional information you want to log.
        Args:
            info: Additional information to log for the current game state.
        """
        self._current['optional'].append(info)

    @property
    def current(self) -> Mapping:
        """
        Returns:
            Current game state logs.
        """
        return self._current

    @property
    def logs(self) -> List[Mapping]:
        """
        Returns: List of all logs from this game.
        """
        return self._current_log

    @property
    def all_logs(self) -> GameLog:
        """
        Returns: GameLog object containing all logs.
        """
        return self._logs

    @property
    def gamefile(self) -> str:
        """
        Returns:
            Game file currently loaded
        """
        return self._gamefile

    def __getitem__(self, index: int) -> Mapping:
        """
        Get a certain log at a given index.
        Args:
            index: index of log to get.
        Returns:
            log at index
        """
        assert index <= len(self._logs)

        return self._current

    def __str__(self) -> str:
        return str(self._current_log)

    def serialize(self) -> List[Mapping]:
        """
        Get serialized mappings of logs.
        Returns:
            List of serialized mappings.
        """
        return self._logs.logs

    def save(self, filename) -> None:
        """
        Saves all logs given a filename
        Returns: None
        """
        self._logs.save(filename)

    def load(self, filename) -> None:
        """
        Loads logs from a file
        Args:
            filename:
                string representing file location
        Returns: None
        """
        self._logs.load(filename)
