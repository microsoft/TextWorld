#!/usr/bin/env python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import argparse
from os.path import join as pjoin

import numpy as np
import networkx as nx

from textworld.render import visualize
from textworld.generator import Game
from textworld.generator.inform7 import Inform7Game
from textworld.generator.chaining import ChainingOptions
from textworld.generator.chaining import sample_quest
from textworld.utils import save_graph_to_svg


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("game",
                        help="Use initial state of the provided game.")
    parser.add_argument("--output", default="./",
                        help="Output folder where to sample the images. Default: %(default)s")
    parser.add_argument("--quest-length", type=int, default=5,
                        help="Minimum nb. of actions required to complete the quest. Default: %(default)s")
    parser.add_argument("--quest-breadth", type=int, default=1,
                        help="Control how non-linear a quest can be.")
    parser.add_argument("--nb-quests", type=int, default=10,
                        help="Number of quests to sample. Default: %(default)s")
    parser.add_argument("--seed", type=int,
                        help="Seed for random generator. Default: always different.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print more information.")

    return parser.parse_args()


def build_tree_from_chains(chains, inform7):
    G = nx.DiGraph()
    root = "root"
    labels = {}
    for chain in chains:
        commands = [root] + inform7.gen_commands_from_actions(chain.actions)
        G.add_nodes_from(commands)
        G.add_edges_from(zip(commands[:-1], commands[1:]))
        labels.update(dict(zip(commands, commands)))

    return G, labels


def print_chains(chains, inform7):
    for i, chain in enumerate(chains):
        commands = inform7.gen_commands_from_actions(chain.actions)
        print("{:2d}. {}".format(i + 1, " > ".join(commands)))


def main():
    args = parse_args()

    # Load game for which to sample quests for.
    game = Game.load(args.game.replace(".ulx", ".json"))

    options = ChainingOptions()
    options.backward = False
    options.max_depth = args.quest_length
    options.max_breadth = args.quest_breadth
    options.rules_per_depth = {}
    options.create_variables = False
    options.rng = np.random.RandomState(args.seed)

    # Sample quests.
    chains = []
    for i in range(args.nb_quests):
        chain = sample_quest(game.world.state, options)
        chains.append(chain)

    inform7 = Inform7Game(game)
    print_chains(chains, inform7)

    # Convert chains to networkx graph/tree
    filename_world = pjoin(args.output, "sample_world.png")
    filename_tree = pjoin(args.output, "sample_tree.svg")
    filename_graph = pjoin(args.output, "sample_graph.svg")
    G, labels = build_tree_from_chains(chains, inform7)
    if len(G) > 0:
        image = visualize(game)
        image.save(filename_world)
        tree = nx.bfs_tree(G, "root")
        save_graph_to_svg(tree, labels, filename_tree)
        save_graph_to_svg(G, labels, filename_graph)
    else:
        try:
            os.remove(filename_world)
            os.remove(filename_tree)
            os.remove(filename_graph)
        except OSError:
            pass


if __name__ == "__main__":
    main()
