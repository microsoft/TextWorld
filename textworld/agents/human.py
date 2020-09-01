# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import sys

from textworld import Agent

prompt_toolkit_available = False
try:
    # For command line history and autocompletion.
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    prompt_toolkit_available = sys.stdout.isatty()
except ImportError:
    pass

try:
    # For command line history when prompt_toolkit is not available.
    import readline  # noqa: F401
except ImportError:
    pass


class HumanAgent(Agent):
    def __init__(self, autocompletion=True, walkthrough=True):
        self.autocompletion = autocompletion
        self.walkthrough = walkthrough

        self._history = None
        if prompt_toolkit_available:
            self._history = InMemoryHistory()

    def reset(self, env):
        # Commands typed by the player are already displayed.
        env.display_command_during_render = False

        if self.autocompletion:
            env.infos.admissible_commands = True

        if self.walkthrough:
            env.infos.policy_commands = True

    def act(self, game_state, reward, done):
        if (self.walkthrough and game_state.intermediate_reward and len(game_state.policy_commands) > 0 and not done):
            text = '[{score:02.1%}|({intermediate_score}): {policy}]\n'.format(
                score=game_state.score,
                intermediate_score=game_state.intermediate_reward,
                policy=" > ".join(game_state.policy_commands)
            )
            print("Walkthrough: {}\n".format(text))

        if prompt_toolkit_available:
            actions_completer = None
            if self.autocompletion and game_state.admissible_commands:
                actions_completer = WordCompleter(game_state.admissible_commands,
                                                  ignore_case=True, sentence=True)
            action = prompt('> ', completer=actions_completer,
                            history=self._history, enable_history_search=True)
        else:
            if self.autocompletion and game_state.admissible_commands:
                print("Available actions: {}\n".format(game_state.admissible_commands))

            action = input('> ')

        return action
