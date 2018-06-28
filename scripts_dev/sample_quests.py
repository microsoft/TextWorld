#!/usr/bin/env python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import argparse
import numpy as np

import textworld
import textworld.agents
import networkx as nx

from textworld.generator import data
from textworld.generator.chaining import ActionTree
from textworld.utils import save_graph_to_svg
from textworld.logic import Variable, Proposition
from textworld.logic import print_chains


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-length", type=int, default=5,
                        help="Minimum nb. of actions required to complete the quest. Default: %(default)s")
    parser.add_argument("--nb-quests", type=int, default=10,
                        help="Number of quests to sample. Default: %(default)s")
    parser.add_argument("--seed", type=int,
                        help="Seed for random generator. Default: always different.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print more information.")

    return parser.parse_args()


def build_tree_from_chains(chains):
    assert chains[0][0].parent.action is None or chains[0][0].action is None
    state = chains[0][0].parent.state if chains[0][0].parent.action is None else chains[0][0].state
    root = ActionTree(state)
    for chain in chains:
        parent = root
        for n1 in chain:
            new_child = True
            for n2 in parent.children:
                if n1.action == n2.action:
                    parent = n2
                    new_child = False
                    break

            if new_child:
                child = ActionTree(n1.state, action=n1.action,
                                   new_propositions=n1.new_propositions)
                parent.children.append(child)
                parent = child

    return root


def main():
    args = parse_args()

    P = Variable("P")
    # I = Variable("I")
    room = Variable("room", "r")
    kitchen = Variable("kitchen", "r")
    state = [Proposition("at", [P, room]),
             Proposition("north_of", [kitchen, room]),
             Proposition("free", [kitchen, room]),
             Proposition("free", [room, kitchen]),
             Proposition("south_of", [room, kitchen])]

    # Sample quests.
    rng = np.random.RandomState(args.seed)
    chains = []
    # rules_per_depth = {0: [data.get_rules()["take/c"], data.get_rules()["take/s"]],
    #                    1: [data.get_rules()["open/c"]],
    #                    }
    rules_per_depth = {0: [data.get_rules()["eat"]],
                       1: data.get_rules().get_matching("take/s.*"),
                       2: data.get_rules().get_matching("go.*"),
                       3: [data.get_rules()["open/d"]],
                       4: [data.get_rules()["unlock/d"]],
                       5: data.get_rules().get_matching("take/s.*", "take/c.*")}

    for i in range(args.nb_quests):
        chain = textworld.logic.sample_quest(state, rng, max_depth=args.quest_length,
                                                       allow_partial_match=True,
                                                       exceptions=[],
                                                       rules_per_depth=rules_per_depth,
                                                       backward=True)
        chains.append(chain[::-1])

    print_chains(chains, verbose=args.verbose)
    actions_tree = build_tree_from_chains(chains)

    # Convert tree to networkx graph/tree
    filename = "sample_tree.svg"
    G, labels = actions_tree.to_networkx()
    if len(G) > 0:
        tree = nx.bfs_tree(G, actions_tree.no)
        save_graph_to_svg(tree, labels, filename, backward=True)
    else:
        try:
            os.remove(filename)
        except:
            pass


if __name__ == "__main__":
    main()
