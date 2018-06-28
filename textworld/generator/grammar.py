# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import List, Callable
from collections import OrderedDict

from textworld.utils import RegexDict
from textworld.logic import Placeholder, Rule, TypeHierarchy
from textworld.generator import data


def get_reverse_action(action):
    rev_rule = data.get_reverse_rules(action)
    if rev_rule is None:
        return None

    return action.inverse(name=rev_rule.name)
