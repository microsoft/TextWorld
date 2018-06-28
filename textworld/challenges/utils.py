# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import numpy as np

from typing import Union, Dict, Optional

from textworld import g_rng


def get_seeds_for_game_generation(seeds: Optional[Union[int, Dict[str, int]]] = None
                                  ) -> Dict[str, int]:
    """ Get all seeds needed for game generation.

    Parameters
    ----------
    seeds : optional
        Seeds for the different generation processes.
        If None, seeds will be sampled from `textworld.g_rng`.
        If a int, it acts as a seed for a random generator that will be
            used to sample the other seeds.
        If dict, the following keys can be set:
                'seed_map': control the map generation;
                'seed_objects': control the type of objects and their location;
                'seed_quest': control the quest generation;
                'seed_grammar': control the text generation;
            For any key missing, a random number gets assigned (sampled from `textworld.g_rng`).

    Returns
    -------
        Seeds that will be used for the game generation.
    """
    keys = ['seed_map', 'seed_objects', 'seed_quest', 'seed_grammar']

    def _key_missing(seeds):
        return not set(seeds.keys()).issuperset(keys)

    if type(seeds) is int:
        rng = np.random.RandomState(seeds)
        seeds = {}
    elif seeds is None or _key_missing(seeds):
        rng = g_rng.next()

    # Check if we need to generate missing seeds.
    for key in keys:
        if key not in seeds:
            seeds[key] = rng.randint(65635)

    return seeds
