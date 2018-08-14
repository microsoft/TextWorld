# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from typing import Tuple, List, Optional, Iterable, Union, Sized, Any, Mapping

from textworld.core import Environment, GameState, Wrapper
from textworld.envs.glulx.git_glulx_ml import GitGlulxMLEnvironment, GlulxGameState


class GlulxLogger(Wrapper):
    def __init__(self, env: GitGlulxMLEnvironment) -> None:
        """
        Wrap around a TextWorld GitGlulxML environment to provide logging capabilities.

        Parameters
        ----------
        :param env:
            The GitGlulxML environment to wrap.
        """
        super().__init__(env)
        self.activate_state_tracking()

        self.serialized_game = env.game.serialize()
        self._gamefile = env.gamefile


    def step(self, command: str) -> Tuple[GlulxGameState, float, bool]:
        """
        Take a step in the environment, save needed information.
        :param command:
            input string for taking an action
        :return:
            GlulxGameState, score and done.
        """
        self._logs.append(self._current)
        self._current = {'optional': []}

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
        Also clears logs.
        """
        self._logs = []
        game_state = super().reset()
        self._current = {'optional': []}
        self._current['done'] = False
        self._current['state'] = game_state.state.serialize()

        return game_state

    def add_commands(self, commands: List[str], scores: Optional[Union[Iterable[float], Sized]]=None) -> None:
        """
        Add custom commands to the logger. Optionally add scores for each command.
        :param commands:
            A list of commands.
        :param scores:
            scores for each command. Must be same size as commands if provided.
        :return:
        """
        command_mapping = commands
        if scores is not None:
            assert len(scores) == len(commands)
            command_mapping = {a: p for a, p in zip(commands, scores)}

        self._current['command_distribution'] = command_mapping

    def add(self, info: Any) -> None:
        """
        Add any additional information you want to log.
        :param info:
            Additional information to log for the current game state.
        """
        self._current['optional'].append(info)

    @property
    def current(self) -> Mapping:
        return self._current

    @property
    def logs(self) -> List[Mapping]:
        """
        Get all logs
        :return: List of all logs
        """
        logs = self._logs[:]
        logs.append(self._current)
        return logs

    @property
    def gamefile(self):
        return self._gamefile

    def __getitem__(self, index: int) -> Mapping:
        """
        Get a certain log at a given index.
        :param index:
            index of log to get.
        :return:
            log at index.
        """
        assert index <= len(self._logs)

        if index < len(self._logs) - 1:
            return self._logs[index]
        return self._current

    def __str__(self) -> str:
        return str(self.logs)

    def serialize(self) -> List[Mapping]:
        """
        Get serialized mappings of logs.
        :return: List of serialized mappings.
        """
        return self.logs