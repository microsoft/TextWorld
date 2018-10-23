# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textwrap
from typing import List, Any, Iterable

from textworld.utils import uniquify


class DependencyTreeElement:
    """
    Representation of an element in the dependency tree.

    The notion of dependency and ordering should be defined for
    these elements.

    Subclasses should override `depends_on`, `__lt__` and
    `__str__` accordingly.
    """

    def __init__(self, value: Any):
        self.value = value
        self.parent = None

    def depends_on(self, other: "DependencyTreeElement") -> bool:
        """
        Check whether this element depends on the `other`.
        """
        return self.value > other.value

    def is_distinct_from(self, others: Iterable["DependencyTreeElement"]) -> bool:
        """
        Check whether this element is distinct from `others`.
        """
        return self.value not in [other.value for other in others]

    def __str__(self) -> str:
        return str(self.value)


class DependencyTree:
    class _Node:
        def __init__(self, element: DependencyTreeElement):
            self.element = element
            self.children = []
            self.parent = None

        def push(self, node: "DependencyTree._Node") -> bool:
            if node == self:
                return True

            added = False
            for child in self.children:
                added |= child.push(node)

            if self.element.depends_on(node.element) and not self.already_added(node):
                node = node.copy()
                self.children.append(node)
                node.element.parent = self.element
                node.parent = self
                return True

            return added

        def already_added(self, node: "DependencyTree._Node") -> bool:
            # We want to avoid duplicate information about dependencies.
            if node in self.children:
                return True

            # Check whether children nodes already contain the dependency
            # information that `node` would bring.
            if not node.element.is_distinct_from((child.element for child in self.children)):
                return True

            return False

        def __iter__(self) -> Iterable["DependencyTree._Node"]:
            for child in self.children:
                yield from list(child)

            yield self

        def __str__(self) -> str:
            node_text = str(self.element)

            txt = [node_text]
            for child in self.children:
                txt.append(textwrap.indent(str(child), "  "))

            return "\n".join(txt)

        def copy(self) -> "DependencyTree._Node":
            node = DependencyTree._Node(self.element)
            for child in self.children:
                child_ = child.copy()
                child_.parent = node
                node.children.append(child_)

            return node

    def __init__(self, element_type: type = DependencyTreeElement, trees: Iterable["DependencyTree"] = []):
        self.roots = []
        self.element_type = element_type
        for tree in trees:
            self.roots += [root.copy() for root in tree.roots]

        self._update()

    def push(self, value: Any, allow_multi_root: bool = False) -> bool:
        """ Add a value to this dependency tree.

        Adding a value already present in the tree does not modify the tree.

        Args:
            value: value to add.
            allow_multi_root: if `True`, allow the value to spawn an
                              additional root if needed.

        """
        element = self.element_type(value)
        node = DependencyTree._Node(element)

        added = False
        for root in self.roots:
            added |= root.push(node)

        if len(self.roots) == 0 or (not added and allow_multi_root):
            self.roots.append(node)
            added = True

        self._update()  # Recompute leaves.
        return added

    def remove(self, value: Any) -> bool:
        """ Remove all leaves having the given value.

        The value to remove needs to belong to at least one leaf in this tree.
        Otherwise, the tree remains unchanged.

        Args:
            value: value to remove from the tree.

        Returns:
            Whether the tree has changed or not.
        """
        if value not in self.leaves_values:
            return False

        root_to_remove = []
        for node in self:
            if node.element.value == value:
                if node.parent is not None:
                    node.parent.children.remove(node)
                else:
                    root_to_remove.append(node)

        for node in root_to_remove:
            self.roots.remove(node)

        self._update()  # Recompute leaves.
        return True

    def _update(self) -> None:
        self._leaves_values = []
        self._leaves_elements = []

        for node in self:
            if len(node.children) == 0:
                self._leaves_elements.append(node.element)
                self._leaves_values.append(node.element.value)

        self._leaves_values = uniquify(self._leaves_values)
        self._leaves_elements = uniquify(self._leaves_elements)

    def copy(self) -> "DependencyTree":
        tree = type(self)(element_type=self.element_type)
        for root in self.roots:
            tree.roots.append(root.copy())

        tree._update()
        return tree

    def __iter__(self) -> Iterable["DependencyTree._Node"]:
        for root in self.roots:
            yield from list(root)

    @property
    def empty(self) -> bool:
        return len(self.roots) == 0

    @property
    def values(self) -> List[Any]:
        return [node.element.value for node in self]

    @property
    def leaves_elements(self) -> List[DependencyTreeElement]:
        return self._leaves_elements

    @property
    def leaves_values(self) -> List[Any]:
        return self._leaves_values

    def __str__(self) -> str:
        return "\n".join(map(str, self.roots))
