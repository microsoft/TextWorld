# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import List, Optional, Dict, Any, Tuple

import gym

from textworld import EnvInfos
from textworld.gym.envs.textworld_batch import TextworldBatchGymEnv


class TextworldGymEnv(TextworldBatchGymEnv):
    metadata = {'render.modes': ['human', 'ansi', 'text']}

    def __init__(self,
                 gamefiles: List[str],
                 request_infos: Optional[EnvInfos] = None,
                 max_episode_steps: Optional[int] = None,
                 action_space: Optional[gym.Space] = None,
                 observation_space: Optional[gym.Space] = None,
                 **kwargs) -> None:
        """ Environment for playing text-based games.

        Arguments:
            gamefiles:
                Paths of every game composing the pool (`*.ulx|*.z[1-8]`).
            request_infos:
                For customizing the information returned by this environment
                (see
                :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
                for the list of available information).

                .. warning:: Only supported for TextWorld games (i.e., that have a corresponding `*.json` file).
            max_episode_steps:
                Number of steps allocated to play each game. Once exhausted, the game is done.
            action_space:
                The action space be used with OpenAI baselines.
                (see :py:class:`textworld.gym.spaces.Word <textworld.gym.spaces.text_spaces.Word>`).
            observation_space:
                The observation space be used with OpenAI baselines
                (see :py:class:`textworld.gym.spaces.Word <textworld.gym.spaces.text_spaces.Word>`).
        """
        super().__init__(gamefiles=gamefiles,
                         request_infos=request_infos,
                         max_episode_steps=max_episode_steps,
                         action_space=action_space,
                         observation_space=observation_space,
                         **kwargs)

    def reset(self) -> Tuple[str, Dict[str, Any]]:
        """ Resets the text-based environment.

        Resetting this environment means starting the next game in the pool.

        Returns:
            A tuple (observation, info) where

            * observation: text observed in the initial state;
            * infos: additional information as requested.
        """
        obs, infos = super().reset()
        return obs[0], {k: v[0] for k, v in infos.items()}

    def step(self, command) -> Tuple[str, Dict[str, Any]]:
        """ Runs a command in the text-based environment.

        Arguments:
            command: Text command to send to the game interpreter.

        Returns:
            A tuple (observation, score, done, info) where

            * observation: text observed in the new state;
            * score: total number of points accumulated so far;
            * done: whether the game is finished or not;
            * infos: additional information as requested.
        """
        obs, scores, dones, infos = super().step([command])
        return obs[0], scores[0], dones[0], {k: v[0] for k, v in infos.items()}
