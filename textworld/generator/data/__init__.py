# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from collections import OrderedDict
import os
import glob
from os.path import join as pjoin
from shutil import copyfile, copytree, rmtree
from typing import Optional

from textworld.logic import GameLogic
from textworld.utils import maybe_mkdir, RegexDict

BUILTIN_DATA_PATH = os.path.dirname(__file__)
LOGIC_DATA_PATH = pjoin(BUILTIN_DATA_PATH, 'logic')
TEXT_GRAMMARS_PATH = pjoin(BUILTIN_DATA_PATH, 'text_grammars')


def _maybe_copyfile(src, dest, force=False, verbose=False):
    if not os.path.isfile(dest) or force:
        copyfile(src=src, dst=dest)
    else:
        if verbose:
            print("Skipping {} (already exists).".format(dest))


def _maybe_copytree(src, dest, force=False, verbose=False):
    if os.path.exists(dest):
        if force:
            rmtree(dest)
        else:
            if verbose:
                print("Skipping {} (already exists).".format(dest))
            return

    copytree(src=src, dst=dest)


def create_data_files(dest: str = './textworld_data', verbose: bool = False, force: bool = False):
    """
    Creates grammar files in the target directory.

    Will NOT overwrite files if they alredy exist (checked on per-file basis).

    Parameters
    ----------
    dest :
        The path to the directory where to dump the data files into.
    verbose :
        Print when skipping an existing file.
    force :
        Overwrite all existing files.
    """

    # Make sure the destination folder exists.
    maybe_mkdir(dest)

    # Knowledge base related files.
    _maybe_copytree(LOGIC_DATA_PATH, pjoin(dest, "logic"), force=force, verbose=verbose)

    # Text generation related files.
    _maybe_copytree(TEXT_GRAMMARS_PATH, pjoin(dest, "text_grammars"), force=force, verbose=verbose)


# Global constants.
_DATA_PATH = None
_TEXT_GRAMMARS_PATH = None

_LOGIC = None
_TYPES = None
_RULES = None
_CONSTRAINTS = None
_REVERSE_RULES = None

INFORM7_COMMANDS = None
INFORM7_EVENTS = None
INFORM7_PREDICATES = None
INFORM7_VARIABLES = None
INFORM7_VARIABLES_DESCRIPTION = None
INFORM7_ADDONS_CODE = None


# def _to_type_tree(types):
#     vtypes = []

#     for vtype in sorted(types):
#         if vtype.parents:
#             parent = vtype.parents[0]
#         else:
#             parent = None
#         vtypes.append(VariableType(vtype.name, vtype.name, parent))

#     return VariableTypeTree(vtypes)


def _to_regex_dict(rules):
    # Sort rules for reproducibility
    # TODO: Only sort where needed
    rules = sorted(rules, key=lambda rule: rule.name)

    rules_dict = OrderedDict()
    for rule in rules:
        rules_dict[rule.name] = rule

    return RegexDict(rules_dict)


def _to_reverse_mapper(rules, reverse_rules):
    def _get_reverse_rule(rule):
        splits = rule.name.split("-")
        name = splits[0]

        reverse_rule_name = reverse_rules.get(name)
        if reverse_rule_name is None:
            return None

        if len(splits) > 1:
            extension = "-".join(splits[1:])
            reverse_rule_name += "-" + extension

        return rules.get(reverse_rule_name)

    return _get_reverse_rule


def load_logic(target_dir: str):
    global _LOGIC
    if _LOGIC:
        return

    paths = [pjoin(target_dir, path) for path in os.listdir(target_dir)]
    logic = GameLogic.load(paths)

    global _TYPES
    # _TYPES = _to_type_tree(logic.types)
    _TYPES = logic.types

    global _RULES
    _RULES = _to_regex_dict(logic.rules.values())

    global _REVERSE_RULES
    _REVERSE_RULES = _to_reverse_mapper(_RULES, logic.reverse_rules)

    global _CONSTRAINTS
    _CONSTRAINTS = _to_regex_dict(logic.constraints.values())

    global INFORM7_COMMANDS
    INFORM7_COMMANDS = {i7cmd.rule: i7cmd.command for i7cmd in logic.inform7.commands.values()}

    global INFORM7_EVENTS
    INFORM7_EVENTS = {i7cmd.rule: i7cmd.event for i7cmd in logic.inform7.commands.values()}

    global INFORM7_PREDICATES
    INFORM7_PREDICATES = {i7pred.predicate.signature: (i7pred.predicate, i7pred.source) for i7pred in logic.inform7.predicates.values()}

    global INFORM7_VARIABLES
    INFORM7_VARIABLES = {i7type.name: i7type.kind for i7type in logic.inform7.types.values()}

    global INFORM7_VARIABLES_DESCRIPTION
    INFORM7_VARIABLES_DESCRIPTION = {i7type.name: i7type.definition for i7type in logic.inform7.types.values()}

    global INFORM7_ADDONS_CODE
    INFORM7_ADDONS_CODE = logic.inform7.code

    _LOGIC = logic


def load_data(target_dir: Optional[str] = None):
    if target_dir is None:
        if os.path.isdir("./textworld_data"):
            target_dir = "./textworld_data"
        else:
            target_dir = BUILTIN_DATA_PATH

    global _DATA_PATH
    _DATA_PATH = target_dir

    # Load knowledge base related files.
    load_logic(pjoin(target_dir, "logic"))

    # Load text generation related files.
    global _TEXT_GRAMMARS_PATH
    _TEXT_GRAMMARS_PATH = pjoin(target_dir, "text_grammars")


def get_logic():
    return _LOGIC


def get_rules():
    return _RULES


def get_constraints():
    return _CONSTRAINTS


def get_reverse_rules(action):
    assert False, "deprecated"  # XXX
    return _REVERSE_RULES(action)


def get_reverse_action(action):
    r_action = action.inverse()
    for rule in get_rules().values():
        r_action.name = rule.name
        if rule.match(r_action):
            return r_action

    return None


def get_types():
    return _TYPES



def sample_type(parent_type, rng, exceptions=[], include_parent=True, probs=None):
    """ Sample an object type given the parent's type. """
    import numpy as np
    types = [t.name for t in get_types().get(parent_type).descendants]
    if include_parent:
        types = [parent_type] + types
    types = [t for t in types if t not in exceptions]

    if probs is not None:
        probs = np.array([probs[t] for t in types], dtype="float")
        probs /= np.sum(probs)

    return rng.choice(types, p=probs)


def count_types(state):
    """ Counts how many objects there are of each type. """
    types_counts = {t.name: 0 for t in get_types()}
    for var in state.variables:
        if get_types().get(var.type).constant:
            continue

        if "_" not in var.name:
            continue

        cpt = int(var.name.split("_")[-1])
        var_type = var.type
        types_counts[var_type] = max(cpt + 1, types_counts[var_type])

    return types_counts


def get_data_path():
    return _DATA_PATH


def get_text_grammars_path():
    return _TEXT_GRAMMARS_PATH
