from typing import Mapping, Any

from textworld import EnvInfos


class Agent:
    """ Interface for any agent playing TextWorld games. """

    @property
    def infos_to_request(self) -> EnvInfos:
        """
        Returns what additional information should be made available at each game step.

        Requested information will be included within the `infos` dictionary
        passed to `Agent.act()`. To request specific information, create a
        :py:class:`textworld.EnvInfos <textworld.envs.wrappers.filter.EnvInfos>`
        and set its attributes to `True` accordingly.

        In addition to the standard information, certain games may have specific
        information that can be requested via the `extras` attribute. Refer to the
        documentation specific to the game to know more (see :py:mod:`textworld.challenges`).

        Example:
            Here is an example of how to request information and retrieve it.

            >>> from textworld import EnvInfos
            >>> request_infos = EnvInfos(description=True, inventory=True)
            ...
            >>> env = gym.make(env_id)
            >>> ob, infos = env.reset()
            >>> print(infos["description"])
            >>> print(infos["inventory"])

        """
        return EnvInfos()

    def act(self, obs: str, score: int, done: bool, infos: Mapping[str, Any]) -> str:
        """
        Acts upon the current list of observations.

        One text command must be returned for each observation.

        Arguments:
            obs: Previous command's feedback (game's narrative).
            score: The score obtained so far.
            done: Whether the game is finished.
            infos: Additional information requested.

        Returns:
            Text command to be performed.
            If episode has ended (i.e. `done` is `True`), the returned
            value is expected to be ignored.
        """
        raise NotImplementedError()
