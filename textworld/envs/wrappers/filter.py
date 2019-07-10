# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Tuple, Mapping, Any, List, Iterable

from textworld.core import Environment, GameState, Wrapper


class EnvInfos:
    """
    Customizing what information will be returned by an environment.

    Information can be requested by setting one or more attributes to True.
    The attribute `extras` should be a list of strings corresponding to
    information specific to certain games.

    """

    __slots__ = ['description', 'inventory', 'location',
                 'facts', 'last_action', 'last_command',
                 'has_won', 'has_lost',
                 'max_score', 'objective',
                 'location_names', 'location_nouns', 'location_adjs',
                 'object_names', 'object_nouns', 'object_adjs',
                 'directions',
                 'verbs', 'command_templates',
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
        #: bool: The last action performed where `None` means it was not a valid action.
        #:       This information changes from one step to another.
        self.last_action = kwargs.get("last_action", False)
        #: bool: The last command performed where `None` means it was not a valid command.
        #:       This information changes from one step to another.
        self.last_command = kwargs.get("last_command", False)
        #: bool: Whether the player won the game.
        #:       This information changes from one step to another.
        self.has_won = kwargs.get("has_won", False)
        #: bool: Whether the player lost the game.
        #:       This information changes from one step to another.
        self.has_lost = kwargs.get("has_lost", False)
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
        #: bool: Name of the possible directions a player can take in the game.
        #:       This information *doesn't* change from one step to another.
        self.directions = kwargs.get("directions", False)
        #: bool: Names of all locations in the game.
        #:       This information *doesn't* change from one step to another.
        self.location_names = kwargs.get("location_names", False)
        #: bool: Noun part of all location names in the game.
        #:       This information *doesn't* change from one step to another.
        self.location_nouns = kwargs.get("location_nouns", False)
        #: bool: Adjective part of all location names in the game.
        #:       This information *doesn't* change from one step to another.
        self.location_adjs = kwargs.get("location_adjs", False)
        #: bool: Names of all locations in the game.
        #:       This information *doesn't* change from one step to another.
        self.object_names = kwargs.get("object_names", False)
        #: bool: Noun part of all object names in the game.
        #:       This information *doesn't* change from one step to another.
        self.object_nouns = kwargs.get("object_nouns", False)
        #: bool: Adjective part of all object names in the game.
        #:       This information *doesn't* change from one step to another.
        self.object_adjs = kwargs.get("object_adjs", False)
        #: bool: Verbs understood by the the game.
        #:       This information *doesn't* change from one step to another.
        self.verbs = kwargs.get("verbs", False)
        #: bool: Templates for commands understood by the the game.
        #:       This information *doesn't* change from one step to another.
        self.command_templates = kwargs.get("command_templates", False)
        #: List[str]: Names of extra information which are game specific.
        self.extras = kwargs.get("extras", [])

        # Check `kwargs` keys are all valid.
        unknown_keys = set(kwargs.keys()) - set(self.__slots__)
        if len(unknown_keys) > 0:
            msg = ("Unknown information requested: {}.".format(sorted(unknown_keys)) +
                   " Available information are: {}".format(sorted(self.__slots__)))
            raise ValueError(msg)

    @property
    def basics(self) -> Iterable[str]:
        """ Information requested excluding the extras. """
        return [slot for slot in self.__slots__ if slot != "extras" and getattr(self, slot)]

    def __len__(self) -> int:
        return len(self.basics) + len(self.extras)


class Filter(Wrapper):
    """
    Environment wrapper to filter what information is made available.

    Requested information will be included within the `infos` dictionary
    returned by `Filter.reset()` and `Filter.step(...)`. To request
    specific information, create a
    :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
    and set the appropriate attributes to `True`. Then, instantiate a `Filter`
    wrapper with the `EnvInfos` object.

    Example:
        Here is an example of how to request information and retrieve it.

        >>> from textworld import EnvInfos
        >>> from textworld.envs.wrappers import Filter
        >>> request_infos = EnvInfos(description=True, inventory=True, extras=["more"])
        ...
        >>> env = Filter(env, request_infos)
        >>> ob, infos = env.reset()
        >>> print(infos["description"])
        >>> print(infos["inventory"])
        >>> print(infos["extra.more"])
    """

    def __init__(self, env: Environment, options: EnvInfos) -> None:
        """
        Arguments:
            env:
                The TextWorld environment to wrap.
            options:
                For customizing the information returned by this environment
                (see
                :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
                for the list of available information).

        """
        super().__init__(env)
        self.options = options

    def _get_requested_infos(self, game_state: GameState):
        infos = {}
        for attr in self.options.basics:
            if hasattr(game_state, attr):
                infos[attr] = getattr(game_state, attr)
            else:
                infos[attr] = getattr(game_state.game, attr)

        if self.options.extras:
            for attr in self.options.extras:
                infos["extra.{}".format(attr)] = game_state.game.extras.get(attr)

        return infos

    def step(self, command: str) -> Tuple[str, float, bool, Mapping[str, Any]]:
        game_state, score, done = super().step(command)
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, score, done, infos

    def reset(self) -> Tuple[str, Mapping[str, Any]]:
        if self.options.admissible_commands or self.options.location:
            self.activate_state_tracking()

        if self.options.intermediate_reward:
            self.activate_state_tracking()
            self.compute_intermediate_reward()

        if self.options.description:
            self._wrapped_env.enable_extra_info("description")

        if self.options.inventory:
            self._wrapped_env.enable_extra_info("inventory")

        game_state = super().reset()
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, infos
