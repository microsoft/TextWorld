# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np

from textworld import Agent


class NaiveAgent(Agent):
    def __init__(self, seed=1234):
        self.seed = seed
        self.rng = np.random.RandomState(self.seed)
        self.actions = ["north", "south", "east", "west", "up", "down",
                        "look", "inventory", "take all", "YES", "wait",
                        "take", "drop", "eat", "attack"]

    def reset(self, env):
        env.display_command_during_render = True

    def act(self, game_state, reward, done):
        action = self.rng.choice(self.actions)
        if action in ["take", "drop", "eat", "attack"]:
            words = game_state.feedback.split()  # Observed words.
            words = [w for w in words if len(w) > 3]  # Ignore most stop words.
            if len(words) > 0:
                action += " " + self.rng.choice(words)

        return action


class RandomCommandAgent(Agent):
    def __init__(self, seed=1234):
        self.seed = seed
        self.rng = np.random.RandomState(self.seed)

    def reset(self, env):
        env.request_infos.admissible_commands = True
        env.display_command_during_render = True

    def act(self, game_state, reward, done):
        if game_state.admissible_commands is None:
            msg = "'--mode random-cmd' is only supported for generated games."
            raise NameError(msg)

        return self.rng.choice(game_state.admissible_commands)
