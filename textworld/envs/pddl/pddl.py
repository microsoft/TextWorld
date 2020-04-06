# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


# -*- coding: utf-8 -*-
import json

from typing import Mapping, Union, Optional

import textworld
from textworld.core import EnvInfos, GameState
from textworld.generator.game import EntityInfo
from textworld.logic import Proposition, Variable

try:
    import fast_downward
    from textworld.envs.pddl import logic as pddl_logic
    fast_downward_missing = False
except ImportError:
    fast_downward_missing = True


class PddlEnv(textworld.Environment):
    """
    Environment for playing games defined by a PDDL file.
    """

    def __init__(self, infos: Optional[EnvInfos] = None) -> None:
        """
        Arguments:
            infos: Information to be included in the game state. By
                       default, only the game's narrative is included.
        """
        if fast_downward_missing:
            msg = "PddlEnv requires fast_downward to be installed. Try running\npip install textworld[pddl]"
            raise ImportError(msg)

        super().__init__(infos)
        self.downward_lib = fast_downward.load_lib()

    def _get_entity_infos(self):
        entity_infos = {v.name: EntityInfo(v.name, v.type) for fact in self._pddl_state.facts for v in fact.arguments}

        for info in entity_infos.values():
            info.name = info.id
            info.definite = "the"
            info.indefinite = "a"

        return entity_infos

    def load(self, filename_or_data: Union[str, Mapping]) -> None:
        try:
            data = json.load(open(filename_or_data))
            self._game_file = filename_or_data
        except TypeError:
            data = filename_or_data
            self._game_file = None

        self._game_data = data
        self._logic = pddl_logic.GameLogic(domain=self._game_data["pddl_domain"], grammar=self._game_data["grammar"])
        self._pddl_state = pddl_logic.PddlState(self.downward_lib, self._game_data["pddl_problem"], self._logic)
        self._entity_infos = self._get_entity_infos()

    def _get_human_readable_fact(self, fact: Proposition) -> Proposition:
        def _get_name(info):
            return info.name if info.name else info.id

        arguments = [Variable(_get_name(self._entity_infos[var.name]), var.type) for var in fact.arguments]
        return Proposition(fact.name, arguments)

    def _gather_infos(self):
        self.state["command_templates"] = sorted(set(action.template for action in self._logic.actions.values()))

        self.state["won"] = self._pddl_state.check_goal()
        self.state["lost"] = False  # TODO: ask planner if the game is lost.

        self.state["_entity_infos"] = dict(self._entity_infos)
        self.state["_facts"] = list(self._pddl_state.facts)
        if self.request_infos.facts:
            self.state["facts"] = list(map(self._get_human_readable_fact, self.state["_facts"]))

        self.state["last_action"] = None
        self.state["_last_action"] = self._last_action
        self.state["_valid_actions"] = list(self._pddl_state.all_applicable_actions())

        mapping = {k: info.name for k, info in self._entity_infos.items()}
        self.state["_valid_commands"] = []
        for action in self.state["_valid_actions"]:
            context = {
                "state": self._pddl_state,
                "facts": list(self._pddl_state.facts),
                "variables": {ph.name: self._entity_infos[var.name] for ph, var in action.mapping.items()},
                "mapping": action.mapping,
                "entity_infos": self._entity_infos,
            }
            action.command_template = self._logic.grammar.derive(action.command_template, context)
            self.state["_valid_commands"].append(action.format_command(mapping))

        # To guarantee the order from one execution to another, we sort the commands.
        # Remove any potential duplicate commands (they would lead to the same result anyway).
        self.state["admissible_commands"] = sorted(set(self.state["_valid_commands"]))

        if self.request_infos.moves:
            self.state["moves"] = self._moves

        if self.request_infos.policy_commands:
            self.state["policy_commands"] = self._pddl_state.replan(self._entity_infos)

    def reset(self):
        self._pddl_state = pddl_logic.PddlState(self.downward_lib, self._game_data["pddl_problem"], self._logic)

        self.prev_state = None
        self.state = GameState()
        self._last_action = None
        self._moves = 0

        context = {
            "state": self._pddl_state,
            "facts": list(self._pddl_state.facts),
            "variables": {},
            "mapping": {},
            "entity_infos": self._entity_infos,
        }

        self.state.feedback = self._logic.grammar.derive("#intro#", context)
        self.state.raw = self.state.feedback
        self._gather_infos()

        if "walkthrough" in self.request_infos.extras:
            self.state["extra.walkthrough"] = self._pddl_state.replan(self._entity_infos)

        return self.state

    def step(self, command: str):
        command = command.strip()
        self.prev_state = self.state

        self.state = GameState()
        self.state.last_command = command

        self._last_action = None
        try:
            # Find the action corresponding to the command.
            idx = self.prev_state["_valid_commands"].index(command)
            self._last_action = self.prev_state["_valid_actions"][idx]
            # An action that affects the state of the game.
            self._pddl_state.apply(self._last_action)

            context = {
                "state": self._pddl_state,
                "facts": list(self._pddl_state.facts),
                "variables": {ph.name: self._entity_infos[var.name] for ph, var in self._last_action.mapping.items()},
                "mapping": self._last_action.mapping,
                "entity_infos": self._entity_infos,
            }

            self.state.feedback = self._logic.grammar.derive(self._last_action.feedback_rule, context)
            self._moves += 1
        except ValueError:
            # We assume nothing happened in the game.
            self.state.feedback = "Nothing happens."

        self.state.raw = self.state.feedback
        self._gather_infos()
        self.state["score"] = 1 if self.state["won"] else 0
        self.state["done"] = self.state["won"] or self.state["lost"]
        return self.state, self.state["score"], self.state["done"]
