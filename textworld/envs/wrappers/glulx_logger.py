# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.
import json

from typing import Tuple, List, Optional, Iterable, Union, Sized, Any, Mapping

from textworld.core import GameState, Wrapper
from textworld.envs.glulx.git_glulx_ml import GitGlulxMLEnvironment, GlulxGameState


class GameLog:
    def __init__(self):
        """
        GameLog object. Allows your to load and save previous game logs.
        """
        self._logs = [[]]
        self._current_game = self._logs[-1]
        self._filename = ''

    def __getitem__(self, idx: int) -> list:
        """
        Gets a particular game log at index idx.
        Args:
            idx: index to retrieve
        Returns:

        """
        assert idx <= len(self._logs)
        return self._logs[idx]

    def __len__(self) -> int:
        return len(self._logs)

    @property
    def current_game(self) -> list:
        """
        Gets current game we're logging.
        Returns: list of logs from current game.
        """
        return self._current_game

    @property
    def logs(self) -> list:
        """
        Get all logs from all games.
        Returns: All logs from all games.
        """
        return self._logs

    def new_game(self):
        """
        Start logs for a new game.
        Returns: log object for current game.
        """
        if len(self._current_game) > 0:
            self._logs.append([])
        self._current_game = self._logs[-1]
        return self._current_game

    def set(self, key: Any, value: Any) -> None:
        """
        Sets value for latest game
        Args:
            key: Key to set
            value: Value to set

        """
        current = self._current_game[-1]
        current[key] = value

    def append_optional(self, value: Any) -> None:
        """
        Appends optional information to current game
        Args:
            value: Value to append

        """
        current = self._current_game[-1]
        if 'optional' not in current:
            current['optional'] = []
        current['optional'].append(value)

    def add_log(self, log: Mapping):
        """
        Adds a new log to our logs
        Args:
            log: Mapping of a log

        """
        self._current_game.append(log)

    def save(self, filename):
        """
        Save current logs to specified file name
        Args:
            filename: File path to save to (should have JSON extension)

        """
        self._filename = filename
        try:
            with open(filename, 'w') as outfile:
                json.dump(self._logs, outfile)
        except TypeError as e:
            raise TypeError('Log not serializable')

    def load(self, filename):
        """
        Loads a JSON object as logs
        Args:
            filename: file path to load.

        """
        self._filename = filename
        with open(filename) as f:
            self._logs= json.load(f)


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

    def step(self, command: str) -> Tuple[GlulxGameState, float, bool]:
        """
        Take a step in the environment.
        Args:
            command: input string for taking an action
        Returns:
            GlulxGameState, score and done.
        """
        new_log = {}
        new_log['optional'] = []
        new_log['command'] = command

        game_state, score, done = super().step(command)
        new_log['feedback'] = game_state.feedback
        new_log['score'] = score
        new_log['done'] = done
        new_log['description'] = game_state.description
        new_log['inventory'] = game_state.inventory
        new_log['state'] = game_state.state.serialize()
        self._logs.add_log(new_log)

        return game_state, score, done

    def reset(self) -> GameState:
        """
        Reset the environment.
        Adds a new game into the logs.
        Returns:
            GameState
        """
        new_log = {}
        self._logs.new_game()

        game_state = super().reset()
        new_log['optional'] = []
        new_log['done'] = False
        new_log['description'] = game_state.description
        new_log['inventory'] = game_state.inventory
        new_log['state'] = game_state.state.serialize()
        self._logs.add_log(new_log)

        return game_state

    def add_commands(self, commands: List[str], scores: Optional[Union[Iterable[float], Sized]]=None) -> None:
        """
        Add custom commands to the logger. Optionally add scores for each command.
        Args:
            commands: A list of commands.
            scores: scores for each command. Must be same size as commands if provided.

        """
        if scores is not None:
            self._logs.set('command_scores', scores)

        self._logs.set('commands', commands)

    def add(self, info: Any) -> None:
        """
        Add any additional information you want to log.
        Args:
            info: Additional information to log for the current game state.
        """
        self._logs.append_optional(info)

    @property
    def current(self) -> Mapping:
        """
        Returns:
            Current game state logs.
        """
        return self._logs.current_game[-1]

    @property
    def logs(self) -> List[Mapping]:
        """
        Returns: List of all logs from this game.
        """
        return self._logs.current_game

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

        return self._logs.current_game[index]

    def __str__(self) -> str:
        return str(self._logs.current_game)

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


