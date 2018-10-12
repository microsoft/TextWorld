# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


"""
.. _coin_collector:

Coin Collector
==============

In this type of game, the world consists in a chain of `quest_length`
rooms with potentially distractors rooms (i.e. leading to a dead end).
The agent stats on one end and has to collect a "coin" object which is
placed at the other end. There is no other objects present in the world
other than the coin to collect.
"""

import numpy as np

from typing import Mapping, Union, Dict, Optional


import textworld
from textworld.generator.graph_networks import reverse_direction

from textworld.utils import encode_seeds
from textworld.generator.game import GameOptions
from textworld.challenges.utils import get_seeds_for_game_generation


def make_game_from_level(level: int, options: Optional[GameOptions] = None) -> textworld.Game:
    """ Make a Coin Collector game of the desired difficulty level.

    Arguments:
        level: Difficulty level (see notes).
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.

    Notes:
        Difficulty levels are defined as follows:

        * Level   1 to 100: Nb. rooms = level, quest length = level
        * Level 101 to 200: Nb. rooms = 2 * (level % 100), quest length = level % 100,
          distractors rooms added along the chain.
        * Level 201 to 300: Nb. rooms = 3 * (level % 100), quest length = level % 100,
          distractors rooms *randomly* added along the chain.
        * ...
    """
    n_distractors = (level // 100)
    options.quest_length = level % 100
    options.nb_rooms = (n_distractors + 1) * options.quest_length
    distractor_mode = "random" if n_distractors > 2 else "simple"
    return make_game(distractor_mode, options)


def make_game(mode: str, options: GameOptions) -> textworld.Game:
    """ Make a Coin Collector game.

    Arguments:
        mode: Mode for the game where

              * `'simple'`: the distractor rooms are only placed orthogonaly
                to the chain. This means moving off the optimal path leads
                immediately to a dead end.
              * `'random'`: the distractor rooms are randomly place along the
                chain. This means a player can wander for a while before
                reaching a dead end.
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.
    """
    if mode == "simple" and float(options.nb_rooms) / options.quest_length > 4:
        msg = ("Total number of rooms must be less than 4 * `quest_length` "
               "when distractor mode is 'simple'.")
        raise ValueError(msg)

    metadata = {}  # Collect infos for reproducibility.
    metadata["desc"] = "Coin Collector"
    metadata["mode"] = mode
    metadata["seeds"] = options.seeds
    metadata["world_size"] = options.nb_rooms
    metadata["quest_length"] = options.quest_length

    rngs = options.rngs
    rng_map = rngs['map']
    rng_grammar = rngs['grammar']

    # Generate map.
    M = textworld.GameMaker()
    M.grammar = textworld.generator.make_grammar(options.grammar, rng=rng_grammar)

    rooms = []
    walkthrough = []
    for i in range(options.quest_length):
        r = M.new_room()
        if i >= 1:
            # Connect it to the previous rooms.
            free_exits = [k for k, v in rooms[-1].exits.items() if v.dest is None]
            src_exit = rng_map.choice(free_exits)
            dest_exit = reverse_direction(src_exit)
            M.connect(rooms[-1].exits[src_exit], r.exits[dest_exit])
            walkthrough.append("go {}".format(src_exit))

        rooms.append(r)

    M.set_player(rooms[0])

    # Add object the player has to pick up.
    obj = M.new(type="o", name="coin")
    rooms[-1].add(obj)

    # Add distractor rooms, if needed.
    chain_of_rooms = list(rooms)
    while len(rooms) < options.nb_rooms:
        if mode == "random":
            src = rng_map.choice(rooms)
        else:
            # Add one distractor room per room along the chain.
            src = chain_of_rooms[len(rooms) % len(chain_of_rooms)]

        free_exits = [k for k, v in src.exits.items() if v.dest is None]
        if len(free_exits) == 0:
            continue

        dest = M.new_room()
        src_exit = rng_map.choice(free_exits)
        dest_exit = reverse_direction(src_exit)
        M.connect(src.exits[src_exit], dest.exits[dest_exit])
        rooms.append(dest)

    # Generate the quest thats by collecting the coin.
    walkthrough.append("take coin")
    # TODO: avoid compiling the game at all (i.e. use the inference engine).
    M.set_quest_from_commands(walkthrough)

    game = M.build()
    game.metadata = metadata
    mode_choice = 0 if mode == "simple" else 1
    uuid = "tw-coin_collector-{specs}-{grammar}-{seeds}"
    uuid = uuid.format(specs=encode_seeds((mode_choice, options.nb_rooms, options.quest_length)),
                       grammar=options.grammar.uuid,
                       seeds=encode_seeds([options.seeds[k] for k in sorted(options.seeds)]))
    game.metadata["uuid"] = uuid
    return game
