import sys
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
        self.gamefile = env.gamefile

        self._logs = []
        self.current_log = {'optional': []}

    def step(self, command: str) -> Tuple[GlulxGameState, float, bool]:
        """
        Take a step in the environment, save needed information.
        :param command:
            input string for taking an action
        :return:
            GlulxGameState, score and done.
        """
        if self.current_log:
            self._logs.append(self.current_log)
            self.current_log = {'optional': []}

        self.current_log['command'] = command

        game_state, score, done = super().step(command)
        self.current_log['feedback'] = game_state.feedback
        self.current_log['score'] = score
        self.current_log['done'] = done
        self.current_log['action'] = game_state.action.serialize()
        self.current_log['state'] = game_state.state.serialize()

        return game_state, score, done

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

        self.current_log['command_distribution'] = command_mapping

    def add(self, info: Any) -> None:
        """
        Add any additional information you want to log.
        :param info:
            Additional information to log for the current game state.
        """
        self.current_log['optional'].append(info)

    @property
    def logs(self) -> List[Mapping]:
        """
        Get all logs
        :return: List of all logs
        """
        logs = self._logs[:]
        logs.append(self.current_log)
        return logs

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
        return self.current_log

    def __str__(self) -> Mapping:
        return self.logs

    def serialize(self) -> List[Mapping]:
        """
        Get serialized mappings of logs.
        :return: List of serialized mappings.
        """
        return self.logs