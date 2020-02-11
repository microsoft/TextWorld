# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld import Agent


class WalkthroughDone(NameError):
    pass


class WalkthroughAgent(Agent):
    """ Agent that simply follows a list of commands. """

    def __init__(self, commands=None):
        self.commands = commands

    def reset(self, env):
        env.display_command_during_render = True
        if self.commands is not None:
            self._commands = iter(self.commands)
            return  # Commands already specified.

        game_state = env.reset()
        if game_state.get("extra.walkthrough") is None:
            msg = "WalkthroughAgent is only supported for games that have a walkthrough."
            raise NameError(msg)

        # Load command from the generated game.
        self._commands = iter(game_state.get("extra.walkthrough"))

    def act(self, game_state, reward, done):
        try:
            action = next(self._commands)
        except StopIteration:
            raise WalkthroughDone()

        action = action.strip()  # Remove trailing \n, if any.
        return action
