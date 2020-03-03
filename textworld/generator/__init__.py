# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import json
import uuid
import numpy as np
from os.path import join as pjoin
from typing import Optional, Mapping, Dict, Union

from numpy.random import RandomState

from textworld import g_rng
from textworld.utils import maybe_mkdir, str2bool
from textworld.logic import State
from textworld.generator.chaining import ChainingOptions, QuestGenerationError
from textworld.generator.chaining import sample_quest
from textworld.generator.world import World
from textworld.generator.game import Game, Quest, Event, GameOptions
from textworld.generator.graph_networks import create_map, create_small_map
from textworld.generator.text_generation import generate_text_from_grammar

from textworld.generator import inform7
from textworld.generator.inform7 import generate_inform7_source, compile_inform7_game
from textworld.generator.inform7 import CouldNotCompileGameError

from textworld.generator.data import KnowledgeBase
from textworld.generator.text_grammar import Grammar
from textworld.generator.maker import GameMaker
from textworld.generator.logger import GameLogger


class GenerationWarning(UserWarning):
    pass


def make_map(n_rooms, size=None, rng=None, possible_door_states=["open", "closed", "locked"]):
    """ Make a map.

    Parameters
    ----------
    n_rooms : int
        Number of rooms in the map.
    size : tuple of int
        Size (height, width) of the grid delimiting the map.
    """
    rng = g_rng.next() if rng is None else rng

    if size is None:
        edge_size = int(np.ceil(np.sqrt(n_rooms + 1)))
        size = (edge_size, edge_size)

    map = create_map(rng, n_rooms, size[0], size[1], possible_door_states)
    return map


def make_small_map(n_rooms, rng=None, possible_door_states=["open", "closed", "locked"]):
    """ Make a small map.

    The map will contains one room that connects to all others.

    Parameters
    ----------
    n_rooms : int
        Number of rooms in the map (maximum of 5 rooms).
    possible_door_states : list of str, optional
        Possible states doors can have.
    """
    rng = g_rng.next() if rng is None else rng

    if n_rooms > 5:
        raise ValueError("Nb. of rooms of a small map must be less than 6 rooms.")

    map_ = create_small_map(rng, n_rooms, possible_door_states)
    return map_


def make_world(world_size, nb_objects=0, rngs=None):
    """ Make a world (map + objects).

    Parameters
    ----------
    world_size : int
        Number of rooms in the world.
    nb_objects : int
        Number of objects in the world.
    """
    if rngs is None:
        rngs = {}
        rng = g_rng.next()
        rngs['map'] = RandomState(rng.randint(65635))
        rngs['objects'] = RandomState(rng.randint(65635))

    map_ = make_map(n_rooms=world_size, rng=rngs['map'])
    world = World.from_map(map_)
    world.set_player_room()
    world.populate(nb_objects=nb_objects, rng=rngs['objects'])
    return world


def make_world_with(rooms, rng=None):
    """ Make a world that contains the given rooms.

    Parameters
    ----------
    rooms : list of textworld.logic.Variable
        Rooms in the map. Variables must have type 'r'.
    """
    map = make_map(n_rooms=len(rooms), rng=rng)
    for (n, d), room in zip(map.nodes.items(), rooms):
        d["name"] = room.name

    world = World.from_map(map)
    world.set_player_room()
    return world


def make_quest(world: Union[World, State], options: Optional[GameOptions] = None):
    state = getattr(world, "state", world)

    if options is None:
        options = GameOptions()

        # By default, exclude quests finishing with: go, examine, look and inventory.
        exclude = ["go.*", "examine.*", "look.*", "inventory.*"]
        options.chaining.rules_per_depth = [options.kb.rules.get_matching(".*", exclude=exclude)]
        options.chaining.rng = options.rngs['quest']

    chains = []
    for _ in range(options.nb_parallel_quests):
        chain = sample_quest(state, options.chaining)
        chains.append(chain)
        state = chain.initial_state  # State might have changed, i.e. options.create_variable is True.

    if options.chaining.backward and hasattr(world, "state"):
        world.state = state  # Quest(s) might have change the world state.

    quests = []
    actions = []
    for chain in reversed(chains):
        for i in range(1, len(chain.nodes)):
            actions.append(chain.actions[i - 1])
            if chain.nodes[i].breadth != chain.nodes[i - 1].breadth:
                event = Event(actions)
                quests.append(Quest(win_events=[event]))

        actions.append(chain.actions[-1])
        event = Event(actions)
        quests.append(Quest(win_events=[event]))

    return quests


def make_grammar(options: Mapping = {}, rng: Optional[RandomState] = None) -> Grammar:
    rng = g_rng.next() if rng is None else rng
    grammar = Grammar(options, rng)
    grammar.check()
    return grammar


def make_game_with(world, quests=None, grammar=None):
    game = Game(world, grammar, quests)
    if grammar is None:
        for var, var_infos in game.infos.items():
            var_infos.name = var.name
    else:
        game = generate_text_from_grammar(game, grammar)

    return game


def make_game(options: GameOptions) -> Game:
    """
    Make a game (map + objects + quest).

    Arguments:
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        Generated game.
    """
    rngs = options.rngs

    # Generate only the map for now (i.e. without any objects)
    world = make_world(options.nb_rooms, nb_objects=0, rngs=rngs)

    # Generate quest(s).
    # By default, exclude quests finishing with: go, examine, look and inventory.
    exclude = ["go.*", "examine.*", "look.*", "inventory.*"]
    options.chaining.rules_per_depth = [options.kb.rules.get_matching(".*", exclude=exclude)]
    options.chaining.backward = True
    options.chaining.create_variables = True
    options.chaining.rng = rngs['quest']
    options.chaining.restricted_types = {"r", "d"}
    quests = make_quest(world, options)

    # If needed, add distractors objects (i.e. not related to the quest) to reach options.nb_objects.
    nb_objects = sum(1 for e in world.entities if e.type not in {'r', 'd', 'I', 'P'})
    nb_distractors = options.nb_objects - nb_objects
    if nb_distractors > 0:
        world.populate(nb_distractors, rng=rngs['objects'])

    grammar = make_grammar(options.grammar, rng=rngs['grammar'])
    game = Game(world, grammar, quests)
    game.metadata["uuid"] = options.uuid

    return game


def compile_game(game: Game, options: Optional[GameOptions] = None):
    """
    Compile a game.

    Arguments:
        game: Game object to compile.
        options:
            For customizing the game generation (see
            :py:class:`textworld.GameOptions <textworld.generator.game.GameOptions>`
            for the list of available options).

    Returns:
        The path to compiled game.
    """
    options = options or GameOptions()

    folder, filename = os.path.split(options.path)
    if not filename:
        filename = game.metadata.get("uuid", str(uuid.uuid4()))

    filename, ext = os.path.splitext(filename)
    if not ext:
        ext = options.file_ext  # Add default extension, if needed.

    source = generate_inform7_source(game)

    maybe_mkdir(folder)
    game_json = pjoin(folder, filename + ".json")
    game_file = pjoin(folder, filename + ext)

    already_compiled = False  # Check if game is already compiled.
    if not options.force_recompile and os.path.isfile(game_file) and os.path.isfile(game_json):
        already_compiled = game == Game.load(game_json)
        msg = ("It's highly unprobable that two games with the same id have different structures."
               " That would mean the generator has been modified."
               " Please clean already generated games found in '{}'.".format(folder))
        assert already_compiled, msg

    if not already_compiled or options.force_recompile:
        game.save(game_json)
        compile_inform7_game(source, game_file)

    return game_file
