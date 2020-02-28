# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


"""
.. _treasure_hunter:

Treasure Hunter
===============


In this type of game, the agent spawns in a randomly generated maze and
must find a specific object which is mentioned in the objective displayed when
game starts. This is a text version of the task proposed in [Parisotto2017]_.


References
----------
.. [Parisotto2017] Emilio Parisotto and Ruslan Salakhutdinov.
   Neural map: Structured memory for deep reinforcement learning.
   arXiv:1702.08360, 2017.
"""

import os
import argparse
from os.path import join as pjoin
from typing import Mapping, Optional

import numpy as np

import textworld
from textworld.utils import uniquify
from textworld.logic import Variable, Proposition
from textworld.generator import QuestGenerationError
from textworld.generator import World
from textworld.generator.game import Quest, Event
from textworld.generator.data import KnowledgeBase
from textworld.generator.vtypes import get_new

from textworld.utils import encode_seeds
from textworld.generator.game import GameOptions
from textworld.challenges import register


KB_PATH = pjoin(os.path.dirname(__file__), "textworld_data")


def build_argparser(parser=None):
    parser = parser or argparse.ArgumentParser()

    group = parser.add_argument_group('Treasure Hunter game settings')
    group.add_argument("--level", required=True, type=int,
                       help="The difficulty level. Must be between 1 and 30 (included).")

    return parser


def make(settings: Mapping[str, str], options: Optional[GameOptions] = None) -> textworld.Game:
    """ Make a Treasure Hunter game of the desired difficulty settings.

    Arguments:
        settings: Difficulty level (see notes). Expected pattern: level[1-30].
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

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

        NB: A game may contain cycles in the map, in which case, there can be
            multiple solutions to solve the game.
    """
    options = options or GameOptions()

    # Load knowledge base specific to this challenge.
    options.kb = KnowledgeBase.load(KB_PATH)

    level = settings["level"]
    if level < 1 or level > 30:
        raise ValueError("Expected level to be within [1-30].")

    if level >= 21:
        mode = "hard"
        options.nb_rooms = 20
        quest_lengths = np.round(np.linspace(3, 20, 10))
        options.quest_length = int(quest_lengths[level - 21])
    elif level >= 11:
        mode = "medium"
        options.nb_rooms = 10
        quest_lengths = np.round(np.linspace(2, 10, 10))
        options.quest_length = int(quest_lengths[level - 11])
    elif level >= 1:
        mode = "easy"
        options.nb_rooms = 5
        quest_lengths = np.round(np.linspace(1, 5, 10))
        options.quest_length = int(quest_lengths[level - 1])

    return make_game(mode, options)


def make_game(mode: str, options: GameOptions) -> textworld.Game:
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
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.
    """
    metadata = {}  # Collect infos for reproducibility.
    metadata["desc"] = "Treasure Hunter"
    metadata["mode"] = mode
    metadata["seeds"] = options.seeds
    metadata["world_size"] = options.nb_rooms
    metadata["quest_length"] = options.quest_length

    rngs = options.rngs
    rng_map = rngs['map']
    rng_objects = rngs['objects']
    rng_quest = rngs['quest']
    rng_grammar = rngs['grammar']

    modes = ["easy", "medium", "hard"]
    if mode == "easy":
        door_states = None
        n_distractors = 0
    elif mode == "medium":
        door_states = ["open"]
        n_distractors = 10
    elif mode == "hard":
        door_states = ["open"]
        n_distractors = 20
        options.chaining.create_variables = True
        options.chaining.allowed_types = ["k"]

    # Generate map.
    map_ = textworld.generator.make_map(n_rooms=options.nb_rooms, rng=rng_map,
                                        possible_door_states=door_states)
    assert len(map_.nodes()) == options.nb_rooms

    world = World.from_map(map_)

    # Add object the player has to pick up.
    types_counts = options.kb.types.count(world.state)
    obj_type = options.kb.types.sample(parent_type='o', rng=rng_objects, include_parent=True)
    var_id = get_new(obj_type, types_counts)
    right_obj = Variable(var_id, obj_type)
    world.add_fact(Proposition("in", [right_obj, world.inventory]))

    # Add containers and supporters to the world.
    types_counts = options.kb.types.count(world.state)
    objects = []
    distractor_types = uniquify(['c', 's']
                                + options.kb.types.descendants('c')
                                + options.kb.types.descendants('s'))
    for i in range(n_distractors):
        obj_type = rng_objects.choice(distractor_types)
        var_id = get_new(obj_type, types_counts)  # This update the types_counts.
        objects.append(Variable(var_id, obj_type))

    world.populate_with(objects, rng=rng_objects)

    # Add object the player should not pick up.
    types_counts = options.kb.types.count(world.state)
    obj_type = options.kb.types.sample(parent_type='o', rng=rng_objects, include_parent=True)
    var_id = get_new(obj_type, types_counts)
    wrong_obj = Variable(var_id, obj_type)
    # Place it anywhere in the world.
    world.populate_with([wrong_obj], rng=rng_objects)

    # Generate a quest that finishes by taking something (i.e. the right
    #  object since it's the only one in the inventory).
    options.chaining.rules_per_depth = [options.kb.rules.get_matching("take.*")]
    restricted_rules = options.kb.rules.get_matching("take.*", "go.*", "open.*", "unlock.*")
    options.chaining.rules_per_depth += [restricted_rules] * (options.quest_length - 1)
    options.chaining.backward = True
    options.chaining.rng = rng_quest

    # Randomly place the player.
    rooms = list(world.rooms)
    rng_map.shuffle(rooms)
    chain = None
    for starting_room in rooms:
        player_fact = world.set_player_room(starting_room)

        try:
            chain = textworld.generator.sample_quest(world.state, options.chaining)
            break
        except QuestGenerationError:
            world.state.remove_fact(player_fact)  # We'll try another starting location.

    if chain is None:
        msg = ("Current map configuration doesn't permit quest of length: {}."
               "Try using a different value for the `--seed` argument.")
        raise QuestGenerationError(msg.format(options.quest_length))

    # Add objects needed for the quest.
    world.state = chain.initial_state
    event = Event(chain.actions)
    quest = Quest(win_events=[event],
                  fail_events=[Event(conditions={Proposition("in", [wrong_obj, world.inventory])})])

    grammar = textworld.generator.make_grammar(options.grammar, rng=rng_grammar)
    game = textworld.generator.make_game_with(world, [quest], grammar)
    game.metadata.update(metadata)
    mode_choice = modes.index(mode)
    uuid = "tw-treasure_hunter-{specs}-{grammar}-{seeds}"
    uuid = uuid.format(specs=encode_seeds((mode_choice, options.nb_rooms, options.quest_length)),
                       grammar=options.grammar.uuid,
                       seeds=encode_seeds([options.seeds[k] for k in sorted(options.seeds)]))
    game.metadata["uuid"] = uuid
    return game


register(name="tw-treasure_hunter",
         desc="Generate a Treasure Hunter game",
         make=make,
         add_arguments=build_argparser)
