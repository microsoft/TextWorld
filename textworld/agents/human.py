# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import sys

from textworld import Agent

prompt_toolkit_available = False
try:
    # For command line history.
    from prompt_toolkit import prompt
    from prompt_toolkit.contrib.completers import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    prompt_toolkit_available = sys.stdout.isatty()
except ImportError:
    pass

try:
    import readline  # For command line history.
except ImportError:
    pass


class HumanAgent(Agent):
    def __init__(self, autocompletion=False, walkthrough=False):
        self.autocompletion = autocompletion
        self.walkthrough = walkthrough

        self._history = None
        if prompt_toolkit_available:
            self._history = InMemoryHistory()

    def reset(self, env):
        if self.autocompletion or self.walkthrough:
            try:
                env.activate_state_tracking()
                env.compute_intermediate_reward()
                # Commands typed by the player are already displayed.
                env.display_command_during_render = False
            except AttributeError:
                msg = ("--hint and --mode=random-cmd are"
                       " only supported for generated games.")
                raise NameError(msg)

    def act(self, game_state, reward, done):
        if (self.walkthrough and game_state._compute_intermediate_reward and len(game_state.policy_commands) > 0 and not game_state.game_ended):
            text = '[{:02.1%}|({}): {}]\n'.format(game_state.score, game_state.intermediate_reward, " > ".join(game_state.policy_commands))
            print("Walkthrough: {}\n".format(text))

        if prompt_toolkit_available:
            actions_completer = None
            if self.autocompletion and hasattr(game_state, "admissible_commands"):
                actions_completer = WordCompleter(game_state.admissible_commands,
                                                  ignore_case=True, sentence=True)
            action = prompt('> ', completer=actions_completer,
                            history=self._history, enable_history_search=True)
        else:
            if self.autocompletion and hasattr(game_state, "admissible_commands"):
                print("Available actions: {}\n".format(game_state.admissible_commands))

            action = input('> ')

        return action
