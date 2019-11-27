# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest
import numpy as np
from copy import deepcopy

from numpy.testing import assert_raises

from textworld.generator.data import KnowledgeBase
from textworld.logic import State, Proposition, Variable
from textworld.generator.vtypes import VariableTypeTree, VariableType
from textworld.generator.vtypes import parse_variable_types, get_new

from textworld.generator import testing


class TestIntegration(unittest.TestCase):

    def setUp(self):
        vtypes = parse_variable_types(testing.VARIABLES_TXT_CONTENT)
        self.types = VariableTypeTree(vtypes)

    def test_parse(self):
        assert len(self.types) == 12
        assert len(self.types.constants) == 2
        assert len(self.types.variables) == 10

    def test_variable_types(self):
        assert self.types.is_constant("P")
        assert self.types.is_constant("I")
        assert set(self.types.descendants('o')) == set(['f', 'k'])
        assert set(self.types.descendants('c')) == set(['oven'])
        assert self.types.is_descendant_of('c', 't')
        assert self.types.is_descendant_of('s', 't')

    def test_parents(self):
        for vtype in self.types:
            for parent in self.types.get_ancestors(vtype):
                assert self.types.is_descendant_of(vtype, parent)

    def test_sample(self):
        rng = np.random.RandomState(1234)
        vtype = self.types.sample("f", rng, include_parent=True)
        assert vtype == "f"

        assert_raises(ValueError, self.types.sample, "f", rng, include_parent=False)

        for t in self.types:
            for _ in range(30):
                vtype = self.types.sample(t, rng, include_parent=True)
                assert self.types.is_descendant_of(vtype, t)

    def test_count(self):
        rng = np.random.RandomState(1234)
        types_counts = {t: rng.randint(2, 10) for t in self.types.variables}

        state = State(KnowledgeBase.default().logic)
        for t in self.types.variables:
            v = Variable(get_new(t, types_counts), t)
            state.add_fact(Proposition("dummy", [v]))

        counts = self.types.count(state)
        for t in self.types.variables:
            assert counts[t] == types_counts[t], (counts[t], types_counts[t])

    def test_serialization_deserialization(self):
        data = self.types.serialize()
        types2 = VariableTypeTree.deserialize(data)
        assert types2.variables_types == types2.variables_types


def test_variable_type_parse():
    vtype = VariableType.parse("name: TYPE")
    assert vtype.name == "name"
    assert vtype.type == "TYPE"
    assert vtype.parent is None
    assert vtype.is_constant

    vtype = VariableType.parse("name: type -> parent")
    assert vtype.name == "name"
    assert vtype.type == "type"
    assert vtype.parent == "parent"
    assert not vtype.is_constant


def test_variable_type_serialization_deserialization():
    signature = "name: type -> parent1"
    vtype = VariableType.parse(signature)
    data = vtype.serialize()
    vtype2 = VariableType.deserialize(data)
    assert vtype == vtype2


def test_get_new():
    rng = np.random.RandomState(1234)
    types_counts = {t: rng.randint(2, 10) for t in KnowledgeBase.default().types}
    orig_types_counts = deepcopy(types_counts)
    for t in KnowledgeBase.default().types:
        name = get_new(t, types_counts)
        splits = name.split("_")
        assert splits[0] == t
        assert int(splits[1]) == orig_types_counts[t]
        assert types_counts[t] == orig_types_counts[t] + 1
