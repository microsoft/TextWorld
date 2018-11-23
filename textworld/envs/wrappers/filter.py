# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Tuple, Mapping, Any

from textworld.core import GameState, Wrapper


class Filter(Wrapper):
    """
    Environment wrapper to filter what information is made available.
    """

    def __init__(self, request_infos) -> None:
        """
        Arguments:
            request_infos:
                Specify which additional information from the `GameState` object
                should be available in the `infos` dictionary returned by
                `env.reset()` and `env.step()`. Possible choices are:

                 * `'description'`: text description of the current room,
                   i.e. output of the `look` command;
                 * `'inventory'`: text listing of the player's inventory,
                   i.e. output of the `inventory` command;
                 * `'max_score'`: maximum reachable score of the game;
                 * `'objective'`: objective of the game described in text;
                 * `'entities'`: names of all entities in the game;
                 * `'verbs'`: verbs understood by the the game;
                 * `'command_templates'`: templates for commands understood
                   by the the game;
                 * `'admissible_commands'`: all commands relevant to the
                   current state;
                 * `'extras:<name>'`: extras information unique to some games;

        """
        self.request_infos = request_infos

    def _get_requested_infos(self, game_state: GameState):
        infos = {}
        for attr in self.request_infos:
            if attr.startswith("extra:"):
                infos[attr] = game_state.extras.get(attr.split(":")[-1])
            else:
                infos[attr] = getattr(game_state, attr)

        return infos

    def step(self, command: str) -> Tuple[str, float, bool, Mapping[str, Any]]:
        game_state, score, done = super().step(command)
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, score, done, infos

    def reset(self) -> Tuple[str, Mapping[str, Any]]:
        if "admissible_commands" in self.request_infos:
            self.activate_state_tracking()

        if "intermediate_reward" in self.request_infos:
            self.activate_state_tracking()
            self.compute_intermediate_reward()

        game_state = super().reset()
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, infos
