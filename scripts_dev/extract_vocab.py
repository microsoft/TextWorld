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
    parser.add_argument("--output", default="vocab.txt",
                        help="Output file containing all words (.txt). Default:%(default)s")
    return parser.parse_args()


def main():
    args = parse_args()
    grammar = Grammar({"theme": args.theme})

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
    text = re.sub(r"[^a-z0-9\- ']", " ", text)
    words = text.split()
    vocab = sorted(set(words))

    print("Vocab size: {} words".format(len(vocab)))

    with open(args.output, "w") as f:
        f.write("\n".join(vocab))


if __name__ == "__main__":
    main()
