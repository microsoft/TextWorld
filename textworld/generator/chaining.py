# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import copy
from collections import Counter
from functools import total_ordering
from numpy.random import RandomState
from typing import Iterable, Mapping, Optional, Sequence

from textworld.generator.data import KnowledgeBase
from textworld.logic import Action, GameLogic, Placeholder, Proposition, Rule, State, Variable


class ChainNode:
    """
    A node in a chain of actions.

    Attributes:
        action: The action to perform at this step.
        depth: This node's depth in the dependency tree.
        breadth: This node's breadth in the dependency tree.
        parent: This node's parent in the dependency tree.
    """

    def __init__(self, action: Action, depth: int, breadth: int, parent: Optional["ChainNode"]):
        self.action = action
        self.depth = depth
        self.breadth = breadth
        self.parent = parent


class Chain:
    """
    An initial state and a chain of actions forming a quest.

    Attributes:
        nodes: The dependency tree of this quest.
        initial_state: The initial state from which the actions start.
        actions: The sequence of actions forming this quest.
    """

    def __init__(self, initial_state: State, nodes: Sequence[ChainNode]):
        self.initial_state = initial_state
        self.nodes = tuple(nodes)
        self.actions = tuple(node.action for node in nodes)

    def __str__(self):
        string = "Chain([\n"
        for action in self.actions:
            string += "    " + str(action) + ",\n"
        string += "])"
        return string


class ChainingOptions:
    """
    Options for customizing the behaviour of chaining.

    Attributes:
        backward:
            Whether to run chaining forwards or backwards.  Forward chaining
            produces a sequence of actions that start at the provided state,
            while backward chaining produces a sequence of actions that end up
            at the provided state.
        min_depth:
            The minimum depth (length) of the generated quests.
        max_depth:
            The maximum depth of the generated quests.
        min_breadth:
            The minimum breadth of the generated quests.  When this is higher
            than 1, the generated quests will have multiple parallel subquests.
            In this case, min_depth and max_depth limit the length of these
            independent subquests, not the total size of the quest.
        max_breadth:
            The maximum breadth of the generated quests.
        subquests:
            Whether to also return incomplete quests, which could be extended
            without reaching the depth or breadth limits.
        independent_chains:
            Whether to allow totally independent parallel chains.
        create_variables:
            Whether new variables may be created during chaining.
        fixed_mapping:
            A fixed mapping from placeholders to variables, for singletons.
        rng:
            If provided, randomize the order of the quests using this random
            number generator.
        logic:
            The rules of the game.
        rules_per_depth:
            A list of lists of rules for restricting the allowed actions at
            certain depths.
        restricted_types:
            A set of types that may not have new variables created.
    """

    def __init__(self):
        self.backward = False
        self.min_depth = 1
        self.max_depth = 1
        self.min_breadth = 1
        self.max_breadth = 1
        self.subquests = False
        self.independent_chains = False
        self.create_variables = False
        self.kb = KnowledgeBase.default()
        self.rng = None
        self.rules_per_depth = []
        self.restricted_types = frozenset()

    @property
    def logic(self) -> GameLogic:
        return self.kb.logic

    @property
    def fixed_mapping(self) -> GameLogic:
        return self.kb.types.constants_mapping

    def get_rules(self, depth: int) -> Iterable[Rule]:
        """
        Get the relevant rules for this depth.

        Args:
            depth: The current depth in the chain.

        Returns:
            The rules that may be applied at this depth in the chain.
        """

        if depth < len(self.rules_per_depth):
            return self.rules_per_depth[depth]
        else:
            # Examine, look and inventory shouldn't be used for chaining.
            exclude = ["examine.*", "look.*", "inventory.*"]
            return self.kb.rules.get_matching(".*", exclude=exclude)

    def check_action(self, state: State, action: Action) -> bool:
        """
        Check if an action should be allowed in this state.

        The default implementation disallows actions that would create new facts
        that don't mention any new variables.

        Args:
            state: The current state.
            action: The action being applied.

        Returns:
            Whether that action should be allowed.
        """

        for prop in action.preconditions:
            if not state.is_fact(prop):
                if all(state.has_variable(var) for var in prop.arguments):
                    # Don't allow creating new predicates without any new variables
                    return False

        return True

    def check_new_variable(self, state: State, type: str, count: int) -> bool:
        """
        Check if a new variable should be allowed to be created in this state.

        Args:
            state: The current state.
            type: The type of variable being created.
            count: The total number of variables of that type.

        Returns:
            Whether that variable should be allowed to be created.
        """

        return type not in self.restricted_types

    def copy(self) -> "ChainingOptions":
        return copy.copy(self)


@total_ordering
class _PartialAction:
    """
    A rule and (partial) assignment for its placeholders.
    """

    def __init__(self, node, rule, mapping):
        self.node = node
        self.rule = rule
        self.mapping = mapping

        # Can't directly compare Variable with None, so split the mapping
        absent = sorted((ph, var) for ph, var in mapping.items() if var is None)
        present = sorted((ph, var) for ph, var in mapping.items() if var is not None)
        self._sort_key = (rule.name, absent, present)

    def __lt__(self, other):
        if isinstance(other, _PartialAction):
            return self._sort_key < other._sort_key
        else:
            return NotImplemented


class _Node:
    """
    A node in a chain being generated.

    Each node is aware of its position (depth, breadth) in the dependency tree
    induced by the chain.  To avoid duplication when generating parallel chains,
    each node stores the actions that have already been used at that depth.
    """

    def __init__(self, parent, dep_parent, state, action, rules, used, depth, breadth):
        self.parent = parent
        self.dep_parent = dep_parent
        self.state = state
        self.action = action
        self.rules = rules
        self.used = used
        self.depth = depth
        self.breadth = breadth


class _Chainer:
    """
    Helper class for the chaining implementation.
    """

    def __init__(self, state, options):
        self.state = state
        self.options = options
        self.backward = options.backward
        self.max_depth = options.max_depth
        self.max_breadth = options.max_breadth
        self.create_variables = options.create_variables
        self.fixed_mapping = options.fixed_mapping
        self.rng = options.rng
        self.constraints = options.logic.constraints.values()

    def root(self) -> _Node:
        """Create the root node for chaining."""
        return _Node(None, None, self.state, None, [], set(), 0, 1)

    def chain(self, node: _Node) -> Iterable[_Node]:
        """
        Perform direct forward/backward chaining.
        """

        if node.depth >= self.max_depth:
            return

        rules = self.options.get_rules(node.depth)

        assignments = self.all_assignments(node, rules)
        if self.rng:
            self.rng.shuffle(assignments)

        used = set()
        for partial in assignments:
            action = self.try_instantiate(node.state, partial)
            if not action:
                continue

            if not self.check_action(node, node.state, action):
                continue

            state = self.apply(node, action)
            if not state:
                continue

            used = used | {action}
            yield _Node(node, node, state, action, rules, used, node.depth + 1, node.breadth)

    def backtrack(self, node: _Node) -> Iterable[_Node]:
        """
        Backtrack to earlier choices to generate parallel quests.
        """

        if node.breadth >= self.max_breadth:
            return

        parent = node
        parents = []
        while parent.dep_parent:
            if parent.depth == 1 and not self.options.independent_chains:
                break
            parents.append(parent)
            parent = parent.dep_parent
        parents = parents[::-1]

        for sibling in parents:
            parent = sibling.dep_parent
            rules = self.options.get_rules(parent.depth)
            assignments = self.all_assignments(node, rules)
            if self.rng:
                self.rng.shuffle(assignments)

            for partial in assignments:
                action = self.try_instantiate(node.state, partial)
                if not action:
                    continue

                if action in sibling.used:
                    continue

                if not self.check_action(parent, node.state, action):
                    continue

                state = self.apply(node, action)
                if not state:
                    continue

                used = sibling.used | {action}
                yield _Node(node, parent, state, action, rules, used, sibling.depth, node.breadth + 1)

    def all_assignments(self, node: _Node, rules: Iterable[Rule]) -> Iterable[_PartialAction]:
        """
        Compute all possible assignments for instantiating the given rules.
        """

        state = node.state

        def allow_partial(ph):
            count = len(state.variables_of_type(ph.type))
            return self.options.check_new_variable(state, ph.type, count)

        assignments = []
        for rule in rules:
            if self.backward:
                rule = rule.inverse()

            for mapping in state.all_assignments(rule, self.fixed_mapping, self.create_variables, allow_partial):
                assignments.append(_PartialAction(node, rule, mapping))

        # Keep everything in a deterministic order
        return sorted(assignments)

    def try_instantiate(self, state: State, partial: _PartialAction) -> Optional[Action]:
        """
        Try to instantiate a partial action, by creating new variables if
        necessary.
        """

        rule, mapping = partial.rule, partial.mapping

        if self.create_variables:
            type_counts = Counter({ph.type: len(state.variables_of_type(ph.type)) for ph in rule.placeholders})

        for ph in rule.placeholders:
            if mapping.get(ph) is None:
                var = self.create_variable(state, ph, type_counts)
                if var:
                    mapping[ph] = var
                else:
                    return None

        return rule.instantiate(mapping)

    def create_variable(self, state, ph, type_counts):
        """Create a new variable of the given type."""

        count = type_counts[ph.type]
        if not self.options.check_new_variable(state, ph.type, count):
            return None

        name = "{}_{}".format(ph.type, count)
        var = Variable(name, ph.type)
        while state.has_variable(var):
            name += "'"
            var = Variable(name, ph.type)

        type_counts[ph.type] += 1
        return var

    def check_action(self, node: _Node, state: State, action: Action) -> bool:
        # Find the last action before a navigation action
        # TODO: Fold this behaviour into ChainingOptions.check_action()
        nav_parent = node
        while nav_parent.action is not None and self._is_navigation(nav_parent.action):
            # HACK: Going through a door is always considered navigation unless the previous action was to open that door.
            parent = nav_parent.parent
            if parent.action is not None and parent.action.name == "open/d":
                break
            if self.backward and action.name == "open/d":
                break
            nav_parent = parent

        if nav_parent.action is not None and not self._is_navigation(action):
            if self.backward:
                recent = action.inverse()
                pre_navigation = recent
                post_navigation = nav_parent.action.inverse()
            else:
                recent = node.action
                pre_navigation = nav_parent.action
                post_navigation = action

            relevant = set(post_navigation.preconditions)

            if len(recent.added & relevant) == 0 or len(pre_navigation.added & relevant) == 0:
                return False

        return self.options.check_action(state, action)

    def _is_navigation(self, action):
        return action.name.startswith("go/")

    def apply(self, node: _Node, action: Action) -> Optional[State]:
        """Attempt to apply an action to the given state."""

        new_state = node.state.copy()
        for prop in action.preconditions:
            new_state.add_fact(prop)

        # Make sure new_state still respects the constraints
        if not self.check_state(new_state):
            return None

        new_state.apply(action)

        if not self.check_state(new_state):
            return None

        # Detect cycles
        state = new_state.copy()
        state.apply(action.inverse())
        while node.action:
            state.apply(node.action.inverse())
            if new_state == state:
                return None
            node = node.parent

        return new_state

    def check_state(self, state: State) -> bool:
        """Check that a state satisfies the constraints."""

        fail = Proposition("fail", [])

        constraints = state.all_applicable_actions(self.constraints)
        for constraint in constraints:
            copy = state.apply_on_copy(constraint)
            if copy and copy.is_fact(fail):
                return False

        return True

    def make_chain(self, node):
        """Create an entire Chain object from a node."""

        nodes = []
        parent = node
        while parent.action:
            nodes.append(parent)
            parent = parent.parent

        mapping = {parent: None}
        for node in reversed(nodes):
            if self.backward:
                action = node.action.inverse()
            else:
                action = node.action

            if node.dep_parent:
                parent = mapping[node.dep_parent]
            else:
                parent = None

            mapping[node] = ChainNode(action, node.depth, node.breadth, parent)

        state = node.state.copy()
        chain = [mapping[node] for node in nodes]
        if not self.backward:
            for node in chain:
                state.apply(node.action.inverse())
            chain = chain[::-1]

        return Chain(state, chain)


def get_chains(state: State, options: ChainingOptions) -> Iterable[Chain]:
    """
    Generates chains of actions (quests) starting from or ending at the given
    state.

    Args:
        state:
            The initial state for chaining.
        options:
            Options to configure chaining behaviour.

    Returns:
        All possible quests according to the constraints.
    """

    chainer = _Chainer(state, options)

    stack = [chainer.root()]
    while stack:
        node = stack.pop()

        no_children = True
        for child in chainer.chain(node):
            stack.append(child)
            no_children = False

        if no_children or options.subquests:
            for child in chainer.backtrack(node):
                stack.append(child)

            if node.depth >= options.min_depth and node.breadth >= options.min_breadth:
                yield chainer.make_chain(node)


def sample_quest(state: State, options: ChainingOptions) -> Optional[Chain]:
    """
    Samples a single chain of actions (a quest) starting from or ending at the
    given state.

    Args:
        state:
            The initial state for chaining.
        options:
            Options to configure chaining behaviour.  Set options.rng to sample
            a random quest.

    Returns:
        A single possible quest.
    """

    for chain in get_chains(state, options):
        return chain

    return None
