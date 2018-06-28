# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


"""
.. _treasure_hunter:

Treasure Hunter
===============


In this type of game, the agent spawns in a randomly generated maze and
must find a specific object mentioned in the objective displayed when the
game stats. This is a text version of the task proposed in [Parisotto2017]_.


References
----------
.. [Parisotto2017] Emilio Parisotto and Ruslan Salakhutdinov.
   Neural map: Structured memory for deep reinforcement learning.
   arXiv:1702.08360, 2017.
"""

import numpy as np

from typing import Mapping, Union, Dict, Optional

import textworld
from textworld.utils import uniquify
from textworld.logic import Variable, Proposition
from textworld.generator import Quest, World
from textworld.generator import data
from textworld.generator.vtypes import get_new
from textworld.challenges.utils import get_seeds_for_game_generation

from textworld.utils import encode_seeds
from textworld.generator.text_grammar import encode_flags


def make_game_from_level(level: int,
                         grammar_flags: Mapping = {},
                         seeds: Optional[Union[int, Dict[str, int]]] = None
                         ) -> textworld.Game:
    """ Make a Treasure Hunter game of the desired difficulty level.

    Arguments:
        level: Difficulty level (see notes).
        grammar_flags: Options for the grammar controlling the text generation
                       process.
        seeds: Seeds for the different generation processes.

               * If `None`, seeds will be sampled from
                 :py:data:`textworld.g_rng <textworld.utils.g_rng>`.
               * If `int`, it acts as a seed for a random generator that will be
                 used to sample the other seeds.
               * If dict, the following keys can be set:

                 * `'seed_map'`: control the map generation;
                 * `'seed_objects'`: control the type of objects and their
                   location;
                 * `'seed_quest'`: control the quest generation;
                 * `'seed_grammar'`: control the text generation.

                 For any key missing, a random number gets assigned (sampled
                 from :py:data:`textworld.g_rng <textworld.utils.g_rng>`).

    Returns:
        game: Generated game.

    Notes:
        Difficulty levels are defined as follows:

        * Level  1 to 10: mode easy, nb. rooms =  5, quest length ranging
          from 1 to  5 as the difficulty increases;
        * Level 11 to 20: mode medium, nb. rooms = 10, quest length ranging
          from 2 to 10 as the difficulty increases;
        * Level 21 to 30: mode hard,   nb. rooms = 20, quest length ranging
          from 3 to 20 as the difficulty increases;

        where the different modes correspond to:

        * Easy: rooms are all empty except where the two objects are
          placed. Also, connections between rooms have no door.
        * Medium: adding closed doors and containers that might need to
          be open in order to find the object.
        * Hard: adding locked doors and containers (necessary keys will in
          the inventory) that might need to be unlocked (and open) in order
          to find the object.
    """
    if level >= 21:
        mode = "hard"
        n_rooms = 20
        quest_lengths = np.round(np.linspace(3, 20, 10))
        quest_length = int(quest_lengths[level - 21])
    elif level >= 11:
        mode = "medium"
        n_rooms = 10
        quest_lengths = np.round(np.linspace(2, 10, 10))
        quest_length = int(quest_lengths[level - 11])
    elif level >= 1:
        mode = "easy"
        n_rooms = 5
        quest_lengths = np.round(np.linspace(1, 5, 10))
        quest_length = int(quest_lengths[level - 1])

    return make_game(mode, n_rooms, quest_length, grammar_flags, seeds)


def make_game(mode: str, n_rooms: int, quest_length: int,
              grammar_flags: Mapping = {},
              seeds: Optional[Union[int, Dict[str, int]]] = None
              ) -> textworld.Game:
    """ Make a Treasure Hunter game.

    Arguments:
        mode: Mode for the game where

              * `'easy'`: rooms are all empty except where the two objects are
                placed. Also, connections between rooms have no door.
              * `'medium'`: adding closed doors and containers that might need
                to be open in order to find the object.
              * `'hard'`: adding locked doors and containers (necessary keys
                will in the inventory) that might need to be unlocked (and open)
                in order to find the object.
        n_rooms: Number of rooms in the game.
        quest_length: How far from the player the object to find should ideally
                      be placed.
        grammar_flags: Options for the grammar controlling the text generation
                       process.
        seeds: Seeds for the different generation processes.

               * If `None`, seeds will be sampled from
                 :py:data:`textworld.g_rng <textworld.utils.g_rng>`.
               * If `int`, it acts as a seed for a random generator that will be
                 used to sample the other seeds.
               * If dict, the following keys can be set:

                 * `'seed_map'`: control the map generation;
                 * `'seed_objects'`: control the type of objects and their
                   location;
                 * `'seed_quest'`: control the quest generation;
                 * `'seed_grammar'`: control the text generation.

                 For any key missing, a random number gets assigned (sampled
                 from :py:data:`textworld.g_rng <textworld.utils.g_rng>`).

    Returns:
        Generated game.
    """
    # Deal with any missing random seeds.
    seeds = get_seeds_for_game_generation(seeds)

    metadata = {}  # Collect infos for reproducibility.
    metadata["desc"] = "Treasure Hunter"
    metadata["mode"] = mode
    metadata["seeds"] = seeds
    metadata["world_size"] = n_rooms
    metadata["quest_length"] = quest_length
    metadata["grammar_flags"] = grammar_flags

    rng_map = np.random.RandomState(seeds['seed_map'])
    rng_objects = np.random.RandomState(seeds['seed_objects'])
    rng_quest = np.random.RandomState(seeds['seed_quest'])
    rng_grammar = np.random.RandomState(seeds['seed_grammar'])

    modes = ["easy", "medium", "hard"]
    if mode == "easy":
        door_states = None
        n_distractors = 0
    elif mode == "medium":
        door_states = ["open", "closed"]
        n_distractors = 10
    elif mode == "hard":
        door_states = ["open", "closed", "locked"]
        n_distractors = 20

    # Generate map.
    map_ = textworld.generator.make_map(n_rooms=n_rooms, rng=rng_map,
                                        possible_door_states=door_states)
    assert len(map_.nodes()) == n_rooms

    world = World.from_map(map_)

    # Randomly place the player.
    starting_room = None
    if len(world.rooms) > 1:
        starting_room = rng_map.choice(world.rooms)

    world.set_player_room(starting_room)

    # Add object the player has to pick up.
    types_counts = data.get_types().count(world.state)
    obj_type = data.get_types().sample(parent_type='o', rng=rng_objects,
                                       include_parent=True)
    var_id = get_new(obj_type, types_counts)
    right_obj = Variable(var_id, obj_type)
    world.add_fact(Proposition("in", [right_obj, world.inventory]))

    # Add containers and supporters to the world.
    types_counts = data.get_types().count(world.state)
    objects = []
    distractor_types = uniquify(['c', 's'] +
                                data.get_types().descendants('c') +
                                data.get_types().descendants('s'))
    for i in range(n_distractors):
        obj_type = rng_objects.choice(distractor_types)
        var_id = get_new(obj_type, types_counts)  # This update the types_counts.
        objects.append(Variable(var_id, obj_type))

    world.populate_with(objects, rng=rng_objects)

    # Add object the player should not pick up.
    types_counts = data.get_types().count(world.state)
    obj_type = data.get_types().sample(parent_type='o', rng=rng_objects,
                                       include_parent=True)
    var_id = get_new(obj_type, types_counts)
    wrong_obj = Variable(var_id, obj_type)
    # Place it anywhere in the world.
    world.populate_with([wrong_obj], rng=rng_objects)

    # Generate a quest that finishes by taking something (i.e. the right
    #  object since it's the only one in the inventory).
    rules_per_depth = {0: data.get_rules().get_matching("take.*")}
    exceptions = ["r", "c", "s", "d"] if mode == "easy" else ["r"]
    chain = textworld.generator.sample_quest(world.state, rng_quest,
                                             max_depth=quest_length,
                                             allow_partial_match=False,
                                             exceptions=exceptions,
                                             rules_per_depth=rules_per_depth,
                                             nb_retry=5,
                                             backward=True)

    # Add objects needed for the quest.
    world.state = chain[0].state
    quest = Quest([c.action for c in chain])
    quest.set_failing_conditions([Proposition("in", [wrong_obj, world.inventory])])

    grammar = textworld.generator.make_grammar(flags=grammar_flags,
                                               rng=rng_grammar)
    game = textworld.generator.make_game_with(world, [quest], grammar)
    game.metadata = metadata
    mode_choice = modes.index(mode)
    uuid = "tw-treasure_hunter-{specs}-{flags}-{seeds}"
    uuid = uuid.format(specs=encode_seeds((mode_choice, n_rooms, quest_length)),
                       flags=encode_flags(grammar_flags),
                       seeds=encode_seeds([seeds[k] for k in sorted(seeds)]))
    game.metadata["uuid"] = uuid
    return game
