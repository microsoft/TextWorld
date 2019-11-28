# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re
from typing import List, Iterable

from textworld.generator.game import Game
from textworld.generator.text_grammar import Grammar


def extract_vocab(games: Iterable[Game]) -> List[str]:
    i7_pattern = re.compile(r'\[[^]]*\]')  # Found in object descriptions.

    text = ""
    seen = set()
    for game in games:
        if game.kb not in seen:
            seen.add(game.kb)
            # Extract words from logic (only stuff related to Inform7).
            text += game.kb.inform7_addons_code + "\n"
            text += " ".join(game.kb.inform7_commands.values()) + "\n"
            text += " ".join(game.kb.inform7_events.values()) + "\n"
            text += " ".join(game.kb.inform7_variables.values()) + "\n"
            text += " ".join(game.kb.inform7_variables.values()) + "\n"
            text += " ".join(t for t in game.kb.inform7_variables_description.values() if t) + "\n"

        if game.grammar.options.uuid not in seen:
            seen.add(game.grammar.options.uuid)
            # Extract words from text grammar.
            grammar = Grammar(game.grammar.options)
            grammar_words = grammar.get_vocabulary()
            text += " ".join(set(grammar_words)).lower() + "\n"

        # Parse game specific entity names and descriptions.
        text += game.objective + "\n"
        for infos in game.infos.values():
            if infos.name:
                text += infos.name + " "

            if infos.desc:
                text += i7_pattern.sub(" ", infos.desc) + "\n"

    # Next strip out all non-alphabetic characters
    text = re.sub(r"[^a-z0-9\-_ ']", " ", text.lower())
    words = text.split()
    vocab = sorted(set(word.strip("-'_") for word in words))
    return vocab
