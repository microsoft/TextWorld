#!/usr/bin/env python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re
import os
import argparse
from os.path import join as pjoin

import numpy as np

from textworld.generator import data
from textworld.generator import Grammar


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("theme",
                        help="Theme from which to extract vocabulary.")

    parser.add_argument("--out", default="vocab.txt",
                        help="Output file containing all words (.txt). Default:%(default)s")

    cfg_parser = parser.add_argument_group('Grammar settings')
    cfg_parser.add_argument("--include-adj", action="store_true",
                            help="Turn on adjectives.")
    cfg_parser.add_argument("--blend-descriptions", action="store_true",
                            help="Blend descriptions across consecutive sentences.")
    cfg_parser.add_argument("--refer-by-name-only", action="store_true",
                            help="Refer to an object using its name only."
                                 " Otherwise, it can referred to using its type"
                                 " (e.g. the red container).")
    cfg_parser.add_argument("--only-last-action", action="store_true",
                            help="Intruction only describes the last action of quest.")
    cfg_parser.add_argument("--blend-instructions", action="store_true",
                            help="Blend instructions across consecutive actions.")

    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    grammar_flags = {
        "theme": args.theme,
        "include_adj": args.include_adj,
        "only_last_action": args.only_last_action,
        "blend_instructions": args.blend_instructions,
        "blend_descriptions": args.blend_descriptions,
        "refer_by_name_only": args.refer_by_name_only,
    }

    rng_grammar = np.random.RandomState(1234)
    grammar = Grammar(grammar_flags, rng=rng_grammar)

    tokens = set()
    filenames = os.listdir(data.get_data_path())
    filenames = [f for f in filenames if f.endswith(".txt")]

    for filename in filenames:
        with open(pjoin(data.get_data_path(), filename)) as f:
            tokens |= set(f.read().split())

    grammar_words = grammar.get_vocabulary()
    tokens |= set(grammar_words)

    text = " ".join(tokens).lower()

    # Next strip out all non-alphabetic characters
    text = re.sub("[^a-z0-9\- ']", " ", text)
    words = text.split()
    vocab = sorted(set(words))

    print("Vocab size: {} words".format(len(vocab)))

    with open(args.out, "w") as f:
        f.write("\n".join(vocab))


if __name__ == "__main__":
    main()
