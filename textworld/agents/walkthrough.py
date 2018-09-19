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

        if not hasattr(env, "game"):
            msg = "WalkthroughAgent is only supported for generated games."
            raise NameError(msg)

        # Load command from the generated game.
        self._commands = iter(env.game.main_quest.commands)

    def act(self, game_state, reward, done):
        try:
            action = next(self._commands)
        except StopIteration:
            raise WalkthroughDone()

        action = action.strip()  # Remove trailing \n, if any.
        return action
