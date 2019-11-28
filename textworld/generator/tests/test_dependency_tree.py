# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import unittest

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

    def test_remove(self):
        tree = DependencyTree(element_type=CustomDependencyTreeElement)
        assert len(tree.roots) == 0
        assert tree.push("G")
        assert tree.remove("G")
        assert len(tree.roots) == 0
        assert list(tree) == []
        assert tree.values == []

        assert tree.push("G")
        assert tree.push("F")
        # Can't pop a non-leaf element.
        assert not tree.remove("G")
        assert len(tree.roots) > 0

        assert set(tree.leaves_values) == set("F")
        assert tree.remove("F")
        assert set(tree.leaves_values) == set("G")

    def test_push(self):
        tree = DependencyTree(element_type=CustomDependencyTreeElement)
        assert len(tree.roots) == 0
        assert set(tree.leaves_values) == set()

        tree.push("G")
        assert set(tree.leaves_values) == set(["G"]), tree.leaves_values
        assert tree.roots[0].element.value == "G"
        assert len(tree.roots[0].children) == 0

        tree.push("F")
        assert set(tree.leaves_values) == set(["F"])

        tree.push("C")
        node = tree.roots[0].children[0].children[0]
        assert set(tree.leaves_values) == set(["C"])
        assert tree.roots[0].element.value == "G"
        assert node.element.value == "C"
        assert len(tree.roots[0].children) == 1
        assert len(node.children) == 0

        # Nothing depends on A at the moment.
        tree.push("A")
        assert set(tree.leaves_values) == set(["C"])

        tree_ = tree.copy()
        tree.push("E")
        assert tree_.values != tree.values
        assert set(tree.leaves_values) == set(["E", "C"])

        # Add the same element twice at the same level doesn't change the tree.
        tree_ = tree.copy()
        tree.push("E")
        assert tree_.values == tree.values
        assert set(tree.leaves_values) == set(["E", "C"])
        # Removing a value not associated to a leaf, does not change the tree.
        assert not tree.remove("Z")
        assert tree_.values == tree.values

        tree.push("A")
        assert set(tree.leaves_values) == set(["A", "C"])

        tree.push("B")
        assert set(tree.leaves_values) == set(["B", "A", "C"])
