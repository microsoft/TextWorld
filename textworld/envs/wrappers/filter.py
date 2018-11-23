# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Tuple, Mapping, Any, List, Iterable

from textworld.core import GameState, Wrapper


class EnvInfos:
    """
    Customizing what information will be returned by an environment.

    Information can be requested by setting one or more attributes to True.
    The attribute `extras` should be a list of strings corresponding to
    information specific to certain games.

    """

    __slots__ = ['description', 'inventory', 'location',
                 'facts',
                 'max_score', 'objective',
                 'entities', 'verbs', 'command_templates',
                 'admissible_commands', 'intermediate_reward',
                 'policy_commands',
                 'extras']

    def __init__(self, **kwargs):
        #: bool: Text description of the current room, i.e. output of the
        #:       `look` command.
        #:       This information changes from one step to another.
        self.description = kwargs.get("description", False)
        #: bool: Text listing of the player's inventory, i.e. output of the
        #:       `inventory` command.
        #:       This information changes from one step to another.
        self.inventory = kwargs.get("inventory", False)
        #: bool: Name of the player's current location.
        #:       This information changes from one step to another.
        self.location = kwargs.get("location", False)
        #: bool: All the facts that are currently true about the world.
        #:       This information changes from one step to another.
        self.facts = kwargs.get("facts", False)
        #: bool: All commands relevant to the current state.
        #:       This information changes from one step to another.
        self.admissible_commands = kwargs.get("admissible_commands", False)
        #: bool: Sequence of commands leading to a winning state.
        #:       This information changes from one step to another.
        self.policy_commands = kwargs.get("policy_commands", False)
        #: bool: Reward (proxy) indicating if the player is making progress.
        #:       This information changes from one step to another.
        self.intermediate_reward = kwargs.get("intermediate_reward", False)
        #: bool: Maximum reachable score of the game.
        #:       This information *doesn't* change from one step to another.
        self.max_score = kwargs.get("max_score", False)
        #: bool: Objective of the game described in text.
        #:       This information *doesn't* change from one step to another.
        self.objective = kwargs.get("objective", False)
        #: bool: Names of all entities in the game.
        #:       This information *doesn't* change from one step to another.
        self.entities = kwargs.get("entities", False)
        #: bool: Verbs understood by the the game.
        #:       This information *doesn't* change from one step to another.
        self.verbs = kwargs.get("verbs", False)
        #: bool: Templates for commands understood by the the game.
        #:       This information *doesn't* change from one step to another.
        self.command_templates = kwargs.get("command_templates", False)
        #: List[str]: Names of extra information which are game specific.
        self.extras = kwargs.get("extras", [])

    @property
    def basics(self) -> Iterable[str]:
        """ Information requested excluding the extras. """
        return [slot for slot in self.__slots__ if slot != "extras" and getattr(self, slot)]

    def __len__(self) -> int:
        return len(self.basics) + len(self.extras)


class Filter(Wrapper):
    """
    Environment wrapper to filter what information is made available.
    """

    def __init__(self, options: EnvInfos) -> None:
        """
        Arguments:
            options:
                For customizing the information returned by this environment
                (see
                :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
                for the list of available information).

        """
        self.options = options

    def _get_requested_infos(self, game_state: GameState):
        infos = {attr: getattr(game_state, attr) for attr in self.options.basics}

        if self.options.extras:
            infos["extras"] = {attr: game_state.extras.get(attr)
                               for attr in self.options.extras}

        return infos

    def step(self, command: str) -> Tuple[str, float, bool, Mapping[str, Any]]:
        game_state, score, done = super().step(command)
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, score, done, infos

    def reset(self) -> Tuple[str, Mapping[str, Any]]:
        if self.options.admissible_commands:
            self.activate_state_tracking()

        if self.options.intermediate_reward:
            self.activate_state_tracking()
            self.compute_intermediate_reward()

        game_state = super().reset()
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, infos
