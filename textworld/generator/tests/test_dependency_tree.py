# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest
from numpy.testing import assert_raises

from textworld.generator.dependency_tree import DependencyTree
from textworld.generator.dependency_tree import DependencyTreeElement


class CustomDependencyTreeElement(DependencyTreeElement):
    DEPENDENCY_RELATIONS = {
        "A": [],
        "B": [],
        "C": [],
        "E": ["A", "B"],
        "G": ["E", "F"],
        "F": ["C", "B", "E"],
    }

    def depends_on(self, other):
        return other.value in self.DEPENDENCY_RELATIONS[self.value]


class TestDependencyTree(unittest.TestCase):

    def test_pop(self):
        tree = DependencyTree(element_type=CustomDependencyTreeElement)
        assert tree.root is None
        tree.push("G")
        tree.pop("G")
        assert tree.root is None

        tree.push("G")
        tree.push("F")
        # Can't pop a non-leaf element.
        assert_raises(ValueError, tree.pop, "G")
        assert tree.root is not None

        assert set(tree.leaves_values) == set("F")
        tree.pop("F")
        assert set(tree.leaves_values) == set("G")

    def test_push(self):
        tree = DependencyTree(element_type=CustomDependencyTreeElement)
        assert tree.root is None
        assert set(tree.leaves_values) == set()

        node = tree.push("G")
        assert set(tree.leaves_values) == set(["G"]), tree.leaves_values
        assert tree.root.element.value == "G"
        assert tree.root is node
        assert len(node.children) == 0

        node = tree.push("F")
        assert set(tree.leaves_values) == set(["F"])

        node = tree.push("C")
        assert set(tree.leaves_values) == set(["C"])
        assert tree.root.element.value == "G"
        assert node.element.value == "C"
        assert len(tree.root.children) == 1
        assert len(node.children) == 0

        # Nothing depends on A at the moment.
        node = tree.push("A")
        assert set(tree.leaves_values) == set(["C"])

        node = tree.push("E")
        assert set(tree.leaves_values) == set(["E", "C"])

        # Add the same element twice at the same level doesn't change the tree.
        node = tree.push("E")
        assert node is None
        assert set(tree.leaves_values) == set(["E", "C"])
        # Cannot remove a value that hasn't been added to the tree.
        assert_raises(ValueError, tree.pop, "Z")

        node = tree.push("A")
        assert set(tree.leaves_values) == set(["A", "C"])

        node = tree.push("B")
        assert set(tree.leaves_values) == set(["B", "A", "C"])
