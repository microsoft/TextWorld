# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import re
from typing import List, Set, Iterable

from textworld.generator.game import Game


def extract_vocab(game: Game) -> Set[str]:
    i7_pattern = re.compile(r'\[[^]]*\]')  # Found in object descriptions.

    text = ""

    # Extract words from logic (only stuff related to Inform7).
    text += game.kb.inform7_addons_code + "\n"
    text += " ".join(game.kb.inform7_commands.values()) + "\n"
    text += " ".join(game.kb.inform7_events.values()) + "\n"
    text += " ".join(game.kb.inform7_variables.values()) + "\n"
    text += " ".join(game.kb.inform7_variables.values()) + "\n"
    text += " ".join(t for t in game.kb.inform7_variables_description.values() if t) + "\n"

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
    vocab = set(word.strip("-'_") for word in words)
    return vocab


def extract_vocab_from_gamefile(gamefile: str) -> Set[str]:
    vocab = set()
    jsonfile = os.path.splitext(gamefile)[0] + ".json"
    if os.path.isfile(jsonfile):
        game = Game.load(jsonfile)
        vocab |= extract_vocab(game)

    if re.search(r"\.z[1-8]$", gamefile):
        # For Z-Machine games, extract vocab using Jericho.
        import jericho
        env = jericho.FrotzEnv(gamefile)
        vocab |= set(entry.word for entry in env.get_dictionary())

    return vocab


def extract_vocab_from_gamefiles(gamefiles: Iterable[str]) -> List[str]:
    vocab = set()
    for gamefile in gamefiles:
        vocab |= extract_vocab_from_gamefile(gamefile)

    return vocab
