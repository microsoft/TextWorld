#!/usr/bin/env python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import argparse

from textworld.text_utils import extract_vocab
from textworld.generator.data import KnowledgeBase
from textworld.generator.text_grammar import GrammarOptions


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("theme",
                        help="Theme from which to extract vocabulary.")
    parser.add_argument("--output", default="vocab.txt",
                        help="Output file containing all words (.txt). Default:%(default)s")
    return parser.parse_args()


def main():
    args = parse_args()

    options = GrammarOptions()
    options.theme = args.theme
    vocab = extract_vocab(options)

    print("Vocab size: {} words".format(len(vocab)))

    with open(args.output, "w") as f:
        f.write("\n".join(vocab))


if __name__ == "__main__":
    main()
