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

import os
import argparse
from os.path import join as pjoin
from typing import Mapping, Optional, Any

import textworld
from textworld.generator.graph_networks import reverse_direction

from textworld.utils import encode_seeds
from textworld.generator.data import KnowledgeBase
from textworld.generator.game import GameOptions, Quest, Event
from textworld.challenges import register


KB_PATH = pjoin(os.path.dirname(__file__), "textworld_data")


def build_argparser(parser=None):
    parser = parser or argparse.ArgumentParser()

    group = parser.add_argument_group('Coin Collector game settings')
    group.add_argument("--level", required=True, type=int,
                       help="The difficulty level. Must be between 1 and 300 (included).")

    return parser


def make(settings: Mapping[str, Any], options: Optional[GameOptions] = None) -> textworld.Game:
    """ Make a Coin Collector game of the desired difficulty settings.

    Arguments:
        settings: Difficulty settings (see notes).
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

            .. warning:: This challenge enforces `options.grammar.allowed_variables_numbering` to be `True`.

    Returns:
        Generated game.

    Notes:
        Difficulty levels are defined as follows:

        * Level   1 to 100: Nb. rooms = 1 * quest length.
        * Level 101 to 200: Nb. rooms = 2 * quest length with
          distractors rooms added along the chain.
        * Level 201 to 300: Nb. rooms = 3 * quest length with
          distractors rooms *randomly* added along the chain.
        * ...

        and where the quest length is set according to ((level - 1) % 100 + 1).
    """
    options = options or GameOptions()

    # Load knowledge base specific to this challenge.
    options.kb = KnowledgeBase.load(KB_PATH)

    # Needed for games with a lot of rooms.
    options.grammar.allowed_variables_numbering = True

    level = settings["level"]
    if level < 1 or level > 300:
        raise ValueError("Expected level to be within [1-300].")

    n_distractors = (level - 1) // 100
    options.quest_length = (level - 1) % 100 + 1
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

            .. warning:: This challenge requires `options.grammar.allowed_variables_numbering` to be `True`.

    Returns:
        Generated game.
    """
    # Needed for games with a lot of rooms.
    assert options.grammar.allowed_variables_numbering

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

    M = textworld.GameMaker(options)

    # Generate map.
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

    # Add a coin for the player to pick up.
    coin = M.new(type="o", name="coin")
    rooms[-1].add(coin)

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
    quest = Quest(win_events=[
        Event(conditions={M.new_fact("in", coin, M.inventory)})
    ])

    M.quests = [quest]

    walkthrough.append("take coin")
    M.set_walkthrough(walkthrough)

    game = M.build()
    game.metadata.update(metadata)
    mode_choice = 0 if mode == "simple" else 1
    uuid = "tw-coin_collector-{specs}-{grammar}-{seeds}"
    uuid = uuid.format(specs=encode_seeds((mode_choice, options.nb_rooms, options.quest_length)),
                       grammar=options.grammar.uuid,
                       seeds=encode_seeds([options.seeds[k] for k in sorted(options.seeds)]))
    game.metadata["uuid"] = uuid
    return game


register(name="tw-coin_collector",
         desc="Generate a Coin Collector game",
         make=make,
         add_arguments=build_argparser)
