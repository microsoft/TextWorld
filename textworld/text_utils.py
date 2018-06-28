# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re
import os
from os.path import join as pjoin

import numpy as np

from textworld.generator import Grammar
from textworld.generator import data


def remove_extra_spaces(output):
    output = output.replace('\n', ' ')
    while '  ' in output:
        output = output.replace('  ', ' ')

    return output.strip()


def extract_location(line):
    # header = output.split("\n")[0]
    location_regex = ["(?P<location>([A-Za-z0-9']+ ?)+)"]
    location = None
    for regex in location_regex:
        match = re.search(regex, line)
        if match is not None:
            location = match.groupdict()['location'].strip()

    # if location is None:
    #     raise ValueError("Missing a regex for location.\nHeader:\n" + header + "\n\nContext:\n" + output)

    # print(location)
    return location


def extract_score(line):
    # header = output.split("\n")[0]
    score_regex = ['Score: *-*(?P<score>[0-9]+)', '(?P<score>[0-9]+)/[0-9]+']
    score = None
    for regex in score_regex:
        match = re.search(regex, line)
        if match is not None:
            score = int(match.groupdict()['score'].strip())

    #if score is None:
    #    print(header)
        # raise ValueError("Missing a regex for score.\nHeader:\n" + header + "\n\nContext:\n" + output)
    # print(score)
    return score


def extract_moves(line):
    #header = output.split("\n")[0]
    moves_regex = ['Moves: *-*(?P<moves>[0-9]+)', 'Turns: *-*(?P<moves>[0-9]+)', '[0-9]+/(?P<moves>[0-9]+)', '[0-9]+/(?P<moves>Lost)']
    moves = None
    for regex in moves_regex:
        match = re.search(regex, line)
        if match is not None:
            moves = match.groupdict()['moves'].strip()

    # if moves is None:
        # raise ValueError("Missing a regex for moves.\nHeader:\n" + header + "\n\nContext:\n" + output)
    # print(moves)
    return moves


def extract_time(line):
    # header = output.split("\n")[0]
    time_regex = ['(?P<time>[0-9]+:[0-9]+ [AaPp][Mm])']
    time = None
    for regex in time_regex:
        match = re.search(regex, line)
        if match is not None:
            time = match.groupdict()['time'].strip()

    # if time is None:
        # raise ValueError("Missing a regex for time.\nHeader:\n" + header + "\n\nContext:\n" + output)
    # print(time)
    return time


def remove_header(text):
    """ Remove score, location, date/time and moves information from output """
    # regex_list = ['[0-9]+/[0-9]+', 'Score:[ ]*[-]*[0-9]+', 'Moves:[ ]*[0-9]+', 'Turns:[ ]*[0-9]+', '[0-9]+:[0-9]+ [AaPp][Mm]', ' [0-9]+ \.'] # that last one is just for murderer.z5

    lines = []
    for line in text.split("\n"):
        if extract_time(line) is not None:
            continue

        if extract_moves(line) is not None:
            continue

        if extract_score(line) is not None:
            continue

        # Custom regex
        regexes = ["(?P<msg>Type 'help')", "(?P<msg>^\.\s*$)"]
        msg = None
        for regex in regexes:
            match = re.search(regex, line)
            if match is not None:
                msg = match.groupdict()['msg'].strip()

        if msg is not None:
            continue

        lines.append(line)

    return "\n".join(lines)


def extract_vocab(grammar_flags):
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

    return vocab
