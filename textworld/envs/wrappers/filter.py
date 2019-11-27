# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Tuple, Mapping, Any

from textworld.core import GameState, Wrapper


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
        >>> env = textworld.start(gamefile, request_infos)
        >>> env = Filter(env)
        >>> ob, infos = env.reset()
        >>> print(infos["description"])
        >>> print(infos["inventory"])
        >>> print(infos["extra.more"])
    """

    def _get_requested_infos(self, game_state: GameState):
        infos = {attr: getattr(game_state, attr) for attr in self.infos.basics}

        if self.infos.extras:
            for attr in self.infos.extras:
                key = "extra.{}".format(attr)
                infos[key] = game_state.get(key)

        return infos

    def step(self, command: str) -> Tuple[str, Mapping[str, Any]]:
        game_state, score, done = super().step(command)
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, score, done, infos

    def reset(self) -> Tuple[str, Mapping[str, Any]]:
        game_state = super().reset()
        ob = game_state.feedback
        infos = self._get_requested_infos(game_state)
        return ob, infos
