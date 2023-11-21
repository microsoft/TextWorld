# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


# -*- coding: utf-8 -*-
from typing import Optional

import textworld
from textworld.core import EnvInfos, GameState
from textworld.generator.game import GameProgression
from textworld.generator.inform7 import Inform7Game


DEFAULT_OBSERVATION = """
[To get text observation use the '.z8' or '.ulx' files instead of the '.json' one.]
"""


class TextWorldEnv(textworld.Environment):
    """
    Environment for playing games by TextWorld.
    """

    def __init__(self, request_infos: Optional[EnvInfos] = None) -> None:
        """
        Arguments:
            request_infos: Information to be included in the game state. By
                           default, only the game's narrative is included.
        """
        super().__init__(request_infos)
        self._gamefile = None
        self._game = None
        self._inform7 = None
        self._last_action = None
        self._prev_state = None
        self._previous_winning_policy = None
        self._current_winning_policy = None
        self._moves = None
        self._game_progression = None

    def load(self, path: str) -> None:
        self._gamefile = path
        self._game = textworld.Game.load(self._gamefile)
        self._game_progression = None
        self._inform7 = Inform7Game(self._game)

    def _gather_infos(self):
        self.state["game"] = self._game
        self.state["command_templates"] = self._game.command_templates
        self.state["verbs"] = self._game.verbs
        self.state["entities"] = self._game.entity_names
        self.state["objective"] = self._game.objective
        self.state["max_score"] = self._game.max_score

        for k, v in self._game.metadata.items():
            self.state["extra.{}".format(k)] = v

        self.state["_game_progression"] = self._game_progression
        self.state["_facts"] = list(self._game_progression.state.facts)

        self.state["won"] = self._game_progression.completed
        self.state["lost"] = self._game_progression.failed

        self.state["_winning_policy"] = self._current_winning_policy
        if self.request_infos.policy_commands:
            self.state["policy_commands"] = []
            if self._game_progression.winning_policy is not None:
                self.state["policy_commands"] = self._inform7.gen_commands_from_actions(self._current_winning_policy)

        if self.request_infos.intermediate_reward:
            self.state["intermediate_reward"] = 0
            if self.state["won"]:
                # The last action led to winning the game.
                self.state["intermediate_reward"] = 1

            elif self.state["lost"]:
                # The last action led to losing the game.
                self.state["intermediate_reward"] = -1

            elif self._previous_winning_policy is None:
                self.state["intermediate_reward"] = 0

            else:
                diff = len(self._previous_winning_policy) - len(self._current_winning_policy)
                self.state["intermediate_reward"] = int(diff > 0) - int(diff < 0)  # Sign function.

        if self.request_infos.facts:
            self.state["facts"] = list(map(self._inform7.get_human_readable_fact, self.state["_facts"]))

        self.state["last_action"] = None
        self.state["_last_action"] = self._last_action
        if self.request_infos.last_action and self._last_action is not None:
            self.state["last_action"] = self._inform7.get_human_readable_action(self._last_action)

        self.state["_valid_actions"] = self._game_progression.valid_actions
        self.state["_valid_commands"] = self._inform7.gen_commands_from_actions(self._game_progression.valid_actions)
        # To guarantee the order from one execution to another, we sort the commands.
        # Remove any potential duplicate commands (they would lead to the same result anyway).
        self.state["admissible_commands"] = sorted(set(self.state["_valid_commands"]))

        if self.request_infos.moves:
            self.state["moves"] = self._moves

    def reset(self):
        self._prev_state = None
        self.state = GameState()
        self._game_progression = GameProgression(self._game, track_quests=True)
        self._last_action = None
        self._previous_winning_policy = None
        self._current_winning_policy = self._game_progression.winning_policy
        self._moves = 0

        self.state.raw = DEFAULT_OBSERVATION
        self.state.feedback = DEFAULT_OBSERVATION
        self._gather_infos()
        return self.state

    def step(self, command: str):
        command = command.strip()
        self._prev_state = self.state

        self.state = GameState()
        self.state.last_command = command
        self.state.raw = DEFAULT_OBSERVATION
        self.state.feedback = DEFAULT_OBSERVATION
        self._previous_winning_policy = self._current_winning_policy

        self._last_action = None
        try:
            # Find the action corresponding to the command.
            idx = self._prev_state["_valid_commands"].index(command)
            self._last_action = self._game_progression.valid_actions[idx]
            # An action that affects the state of the game.
            self._game_progression.update(self._last_action)
            self._current_winning_policy = self._game_progression.winning_policy
            self._moves += 1
        except ValueError:
            self.state.feedback = "Invalid command."
            pass  # We assume nothing happened in the game.

        self._gather_infos()
        self.state["score"] = self._game_progression.score
        self.state["done"] = self.state["won"] or self.state["lost"]
        return self.state, self.state["score"], self.state["done"]

    def copy(self) -> "TextWorldEnv":
        """ Return a copy of this environment.

        It is safe to call `step` and `reset` on the copied environment.

        .. warning:: The `Game` and `Inform7Game` private objects are *soft* copies.
        """
        env = TextWorldEnv()

        # Copy core Environment's attributes.
        env.state = self.state.copy()
        env.request_infos = self.request_infos.copy()

        env._gamefile = self._gamefile
        env._game = self._game  # Reference
        env._inform7 = self._inform7  # Reference

        env._prev_state = self._prev_state.copy() if self._prev_state is not None else None
        env._last_action = self._last_action
        env._moves = self._moves
        if self._previous_winning_policy is not None:
            env._previous_winning_policy = tuple(self._previous_winning_policy)

        if self._current_winning_policy is not None:
            env._current_winning_policy = tuple(self._current_winning_policy)

        if self._game_progression is not None:
            env._game_progression = self._game_progression.copy()

        return env
