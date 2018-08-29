# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textwrap
from typing import List, Any

from textworld.utils import uniquify


class DependencyTreeElement:
    """
    Representation of an element in the dependency tree.

    The notion of dependency and ordering should be defined for
    these elements.

    Subclasses should override `depends_on`, `__lt__` and
    `__str__` accordingly.
    """

    def __init__(self, value):
        self.value = value

    def depends_on(self, other):
        """
        Check whether this element depends on the `other`.
        """
        return self.value > other.value

    def is_distinct_from(self, others):
        """
        Check whether this element is distinct from `others`.
        """
        return self.value not in [other.value for other in others]

    def __str__(self):
        return str(self.value)


class DependencyTree:
    class _Node:
        def __init__(self, element):
            self.element = element
            self.children = []

        def push(self, node):
            if node == self:
                return True
            
            added = False
            for child in self.children:
                added |= child.push(node)

            if self.element.depends_on(node.element) and not self.already_added(node):
                self.children.append(node)
                return True

            return added

        def already_added(self, node):
            # We want to avoid duplicate information about dependencies.
            if node in self.children:
                return True

            # Check whether children nodes already contain the dependency
            # information that `node` would bring.
            if not node.element.is_distinct_from((child.element for child in self.children)):
                return True

            return False

        def __str__(self):
            node_text = str(self.element)

            txt = [node_text]
            for child in self.children:
                txt.append(textwrap.indent(str(child), "  "))

            return "\n".join(txt)

        def copy(self):
            node = DependencyTree._Node(self.element)
            node.children = [child.copy() for child in self.children]
            return node

    def __init__(self, element_type=DependencyTreeElement, trees=[]):
        self.roots = []
        self.element_type = element_type
        for tree in trees:
            self.roots += [root.copy() for root in tree.roots]

        self._update()

    def push(self, value: Any, allow_multi_root: bool = False):
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

        # Recompute leaves.
        self._update()

    def pop(self, value):
        if value not in self.leaves_values:
            raise ValueError("That element is not a leaf: {!r}.".format(value))

        def _visit(node):
            for child in list(node.children):
                if child.element.value == value:
                    node.children.remove(child)

        root_to_remove = [] 
        for i, root in enumerate(self.roots):
            self._postorder(root, _visit)
            if root.element.value == value:
                root_to_remove.append(i)
        
        for i in root_to_remove[::-1]:
            del self.roots[i]

        # Recompute leaves.
        self._update()

    def _postorder(self, node, visit):
        for child in node.children:
            self._postorder(child, visit)

        visit(node)

    def _update(self):
        self._leaves_values = []
        self._leaves_elements = []

        def _visit(node):
            if len(node.children) == 0:
                self._leaves_elements.append(node.element)
                self._leaves_values.append(node.element.value)

        for root in self.roots:
            self._postorder(root, _visit)

        self._leaves_values = uniquify(self._leaves_values)
        self._leaves_elements = uniquify(self._leaves_elements)

    def copy(self):
        tree = type(self)(element_type=self.element_type)
        for root in self.roots:
            tree.roots.append(root.copy())
        
        tree._update()
        return tree

    def tolist(self) -> List[Any]:
        values = []

        def _visit(node):
            values.append(node.element.value)

        for root in self.roots:
            self._postorder(root, _visit)
    
        return values

    @property
    def leaves_elements(self):
        return self._leaves_elements

    @property
    def leaves_values(self):
        return self._leaves_values

    def __str__(self):
        return "\n".join(map(str, self.roots))

