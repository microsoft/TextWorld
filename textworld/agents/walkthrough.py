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
        from textworld.generator.game import GameProgression, Quest
        from textworld.generator.inform7 import gen_commands_from_actions

        game_progression = GameProgression(env.game)
        main_quest = Quest(actions=game_progression.winning_policy)
        commands = gen_commands_from_actions(main_quest.actions, env.game.infos)
        self._commands = iter(commands)

    def act(self, game_state, reward, done):
        try:
            action = next(self._commands)
        except StopIteration:
            raise WalkthroughDone()

        action = action.strip()  # Remove trailing \n, if any.
        return action
