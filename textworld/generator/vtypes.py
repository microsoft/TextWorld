# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from collections import deque, namedtuple
import numpy as np
import re
from typing import List

from textworld.logic import Placeholder, Variable


_WHITESPACE = re.compile(r"\s+")
_ID = re.compile(r"[\w/']+")
_PUNCT = ["::", ":", "$", "(", ")", ",", "&", "->"]

_Token = namedtuple("_Token", ("type", "value"))

def _tokenize(expr):
    """
    Helper tokenizer for logical expressions.
    """

    tokens = deque()

    i = 0
    while i < len(expr):
        m = _WHITESPACE.match(expr, i)
        if m:
            i = m.end()
            continue

        m = _ID.match(expr, i)
        if m:
            tokens.append(_Token("id", m.group()))
            i = m.end()
            continue

        for punct in _PUNCT:
            end = i + len(punct)
            chunk = expr[i:end]
            if chunk == punct:
                tokens.append(_Token(chunk, chunk))
                i = end
                break
        else:
            raise ValueError("Unexpected character `{}`.".format(expr[i]))

    return tokens


def _lookahead(tokens, type):
    return tokens and tokens[0].type == type


def _expect(tokens, type):
    if type == "id":
        human_type = "an identifier"
    else:
        human_type = "`{}`".format(type)

    if not tokens:
        raise ValueError("Expected {}; found end of input.".format(human_type))

    if tokens[0].type != type:
        raise ValueError("Expected {}; found `{}`.".format(human_type, tokens[0].value))

    return tokens.popleft()


class NotEnoughNounsError(NameError):
    pass


class VariableType:
    def __init__(self, type, name, parent=None):
        self.type = type
        self.name = name
        self.parent = parent
        self.children = []
        # If the type starts with an upper case letter, it is a constant.
        self.is_constant = self.type[0] == self.type.upper()[0]

    @classmethod
    def parse(cls, expr: str) -> "VariableType":
        """
        Parse a variable type expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name: type -> parent1 & parent2`
            or `name: type` for root node.
        """
        tokens = _tokenize(expr)
        name = _expect(tokens, "id").value
        _expect(tokens, ":")
        type = _expect(tokens, "id").value

        parent = None
        if _lookahead(tokens, "->"):
            tokens.popleft()
            parent = _expect(tokens, "id").value

        return cls(type, name, parent)

    def __eq__(self, other):
        return (isinstance(other, VariableType) and
                self.name == other.name and
                self.type == other.type and
                self.parent == other.parent)

    def __str__(self):
        signature = "{}: {}".format(self.name, self.type)
        if self.parent is not None:
            signature += " -> " + self.parent

        return signature

    def serialize(self) -> str:
        return str(self)

    @classmethod
    def deserialize(cls, data: str) -> "VariableType":
        return cls.parse(data)


def parse_variable_types(content: str):
    """
    Parse a list VariableType expressions.
    """
    vtypes = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#") or line == "":
            continue

        vtypes.append(VariableType.parse(line))

    return vtypes


class VariableTypeTree:
    """
    Manages hierarchy of types defined in ./grammars/variables.txt.
    Used for extending the rules.
    """
    CHEST = 'c'
    SUPPORTER = 's'
    CLASS_HOLDER = [CHEST, SUPPORTER]

    def __init__(self, vtypes: List[VariableType]):
        self.variables_types = {vtype.type: vtype for vtype in vtypes}

        # Make some convenient attributes.
        self.types = [vt.type for vt in vtypes]
        self.names = [vt.name for vt in vtypes]
        self.constants = [t for t in self if self.is_constant(t)]
        self.variables = [t for t in self if not self.is_constant(t)]
        self.constants_mapping = {Placeholder(c): Variable(c) for c in self.constants}

        # Adjust variable type's parent and children references.
        for vt in vtypes:
            if vt.parent is not None:
                vt_parent = self[vt.parent]
                vt_parent.children.append(vt.type)

    @classmethod
    def load(cls, path: str):
        """
        Read variables from text file.
        """
        with open(path) as f:
            vtypes = parse_variable_types(f.read())
            return cls(vtypes)

    def __getitem__(self, vtype):
        """ Get VariableType object from its type string. """
        vtype = vtype.rstrip("'")
        return self.variables_types[vtype]

    def __contains__(self, vtype):
        vtype = vtype.rstrip("'")
        return vtype in self.variables_types

    def __iter__(self):
        return iter(self.variables_types)

    def __len__(self):
        return len(self.variables_types)

    def is_constant(self, vtype):
        return self[vtype].is_constant

    def descendants(self, vtype):
        """Given a variable type, return all possible descendants."""
        descendants = []
        for child_type in self[vtype].children:
            descendants.append(child_type)
            descendants += self.descendants(child_type)

        return descendants

    def get_description(self, vtype):
        if vtype in self.types:
            return self.names[self.types.index(vtype)]
        else:
            return vtype

    def get_ancestors(self, vtype):
        """ List all ancestors of a type where the closest ancetors are first. """
        vtypes = []
        if self[vtype].parent is not None:
            vtypes.append(self[vtype].parent)
            vtypes.extend(self.get_ancestors(self[vtype].parent))

        return vtypes

    def is_descendant_of(self, child, parents):
        """ Return if child is a descendant of parent """
        if not isinstance(parents, list):
            parents = [parents]

        for parent in parents:
            if child == parent or child in self.descendants(parent):
                return True

        return False

    def sample(self, parent_type, rng, exceptions=[], include_parent=True, probs=None):
        """ Sample an object type given the parent's type. """
        types = self.descendants(parent_type)
        if include_parent:
            types = [parent_type] + types
        types = [t for t in types if t not in exceptions]

        if probs is not None:
            probs = np.array([probs[t] for t in types], dtype="float")
            probs /= np.sum(probs)

        return rng.choice(types, p=probs)

    def count(self, state):
        """ Counts how many objects there are of each type. """
        types_counts = {t: 0 for t in self}
        for var in state.variables:
            if self.is_constant(var.type):
                continue

            if "_" not in var.name:
                continue

            cpt = int(var.name.split("_")[-1])
            var_type = var.type
            types_counts[var_type] = max(cpt + 1, types_counts[var_type])

        return types_counts

    def serialize(self) -> List:
        return [vtype.serialize() for vtype in self.variables_types.values()]

    @classmethod
    def deserialize(cls, data: List) -> "VariableTypeTree":
        vtypes = [VariableType.deserialize(d) for d in data]
        return cls(vtypes)


def get_new(type, types_counts, max_types_counts=None):
    """ Get the next available id for a given type. """
    if max_types_counts is not None and types_counts[type] >= max_types_counts[type]:
        raise NotEnoughNounsError()

    new_id = "{}_{}".format(type, types_counts[type])
    types_counts[type] += 1
    return new_id
