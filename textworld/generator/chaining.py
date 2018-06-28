# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld.generator import data
from textworld.logic import Proposition, Variable
from textworld.generator.vtypes import get_new, NotEnoughNounsError


def _hash_state(state):
    return frozenset(state.facts)


class ActionTree(object):

    def __init__(self, state, action=None, new_propositions=[]):
        self.action = action
        self.new_propositions = new_propositions
        self.children = []
        self.state = state
        self.hash = _hash_state(state)
        self.hashes = {self.hash}  # Set of seen hashes.
        self.parent = None
        self.depth = 0

    def set_parent(self, parent):
        self.parent = parent
        self.depth = parent.depth + 1

    def get_path(self):
        chain = [self]
        while chain[-1].parent is not None:
            chain.append(chain[-1].parent)

        return chain[::-1][1:]  # Do not include root.

    def traverse_preorder(self, subquests=False):
        """
        Generate chains from Actiontree. If subquests
        True yield all chains else only full chains from root to leaf.
        """
        chain = []
        to_visit = self.children[::-1]
        while len(to_visit) > 0:
            node = to_visit.pop()
            chain = chain + [node]
            to_visit += node.children[::-1]

            if subquests or len(node.children) == 0:
                yield chain

            # Backtrack chain
            while len(to_visit) > 0 and len(chain) > 0 and to_visit[-1] not in chain[-1].children:
                chain = chain[:-1]

    def to_networkx(self):
        import networkx as nx
        G = nx.Graph()
        labels = {}
        cpt = [0]

        def _recur(parent):
            for i, c in enumerate(parent.children):
                cpt[0] += 1
                c.no = str(cpt[0])
                G.add_edge(parent.no, c.no)
                params = ", ".join(map(str, c.action.variables))
                labels[c.no] = "{}({})".format(c.action.name, params)
                _recur(c)

        self.no = str(cpt[0])
        labels[self.no] = repr(self.action)  # Should be None.
        _recur(self)
        return G, labels


def get_failing_constraints(state):
    fail = Proposition("fail", [])

    failed_constraints = []
    constraints = state.all_applicable_actions(data.get_constraints().values())
    for constraint in constraints:
        if state.is_applicable(constraint):
            # Optimistically delay copying the state
            copy = state.copy()
            copy.apply(constraint)

            if copy.is_fact(fail):
                failed_constraints.append(constraint)

    return failed_constraints


def check_state(state):
    fail = Proposition("fail", [])
    debug = Proposition("debug", [])

    constraints = state.all_applicable_actions(data.get_constraints().values())
    for constraint in constraints:
        if state.is_applicable(constraint):
            # Optimistically delay copying the state
            copy = state.copy()
            copy.apply(constraint)

            if copy.is_fact(fail):
                return False

    return True


def maybe_instantiate_variables(rule, mapping, state, max_types_counts=None):
    types_counts = data.get_types().count(state)

    # Instantiate variables if needed
    try:
        for ph in rule.placeholders:
            if mapping.get(ph) is None:
                name = get_new(ph.type, types_counts, max_types_counts)
                mapping[ph] = Variable(name, ph.type)
    except NotEnoughNounsError:
        return None

    return rule.instantiate(mapping)


def _assignment_sort_key(assignment):
    rule, mapping = assignment

    # Can't directly compare Variable with None, so split the mapping
    absent = sorted(item for item in mapping.items() if item[1] is None)
    present = sorted(item for item in mapping.items() if item[1] is not None)

    return (rule.name, absent, present)


def _get_all_assignments(state, rules, partial=False, constrained_types=None, backward=False):
    assignments = []
    for rule in rules:
        if backward:
            rule = rule.inverse()
        for mapping in state.all_assignments(rule, data.get_types().constants_mapping, partial, constrained_types):
            assignments.append((rule, mapping))

    # Keep everything in a deterministic order
    return sorted(assignments, key=_assignment_sort_key)


def _is_navigation(action):
    return action.name.startswith("go/")


def _try_instantiation(rule, mapping, parent, allow_parallel_chains, max_types_counts, backward):
    action = maybe_instantiate_variables(rule, mapping, parent.state, max_types_counts=max_types_counts)
    if not action:
        return None

    new_state = parent.state.copy()

    new_propositions = []
    for prop in action.preconditions:
        if not new_state.is_fact(prop):
            if all(parent.state.has_variable(var) for var in prop.arguments):
                # Don't allow creating new predicates without any new variables
                return None
            new_state.add_fact(prop)
            new_propositions.append(prop)

    # Make sure new_state still respect the constraints.
    if not check_state(new_state):
        return None # Invalid state detected

    parent_hashes = parent.hashes | {_hash_state(new_state)}

    new_state.apply(action)

    # Some debug checks.
    assert check_state(new_state)

    if backward:
        action = action.inverse()
    child = ActionTree(new_state, action, new_propositions)

    if child.hash in parent_hashes:
        return None  # Cycle detected.

    # Keep track of all previous hashes.
    child.hashes |= parent_hashes

    # Discard parallel_chains if needed.
    last_action_before_navigation = parent
    while last_action_before_navigation.action is not None and _is_navigation(last_action_before_navigation.action):
        # HACK: Going through a door is consider always as navigation unless the previous action was to open that door.
        if last_action_before_navigation.parent.action is not None and last_action_before_navigation.parent.action.name == "open/d":
            break
        if backward and action.name == "open/d":
            break

        last_action_before_navigation = last_action_before_navigation.parent

    if last_action_before_navigation.action is not None and not allow_parallel_chains and not _is_navigation(action):
        parent_rhs = parent.action.postconditions if not backward else action.postconditions
        parent_lhs = parent.action.preconditions if not backward else action.preconditions
        recent_changes = set(parent_rhs) - set(parent_lhs)
        last_action_before_navigation_rhs = last_action_before_navigation.action.postconditions if not backward else action.postconditions
        last_action_before_navigation_lhs = last_action_before_navigation.action.preconditions if not backward else action.preconditions
        action_lhs = action.preconditions if not backward else last_action_before_navigation.action.preconditions
        changes_before_navigation = set(last_action_before_navigation_rhs) - set(last_action_before_navigation_lhs)
        if len(recent_changes & set(action_lhs)) == 0 or len(changes_before_navigation & set(action_lhs)) == 0:
            return None # Parallel chain detected.

    return child


def _get_chains(state, root=None, max_depth=1,
                    allow_parallel_chains=False, allow_partial_match=False,
                    rng=None, exceptions=[], max_types_counts=None,
                    rules_per_depth={}, backward=False):

    root = ActionTree(state) if root is None else root

    openset = [root]
    while len(openset) > 0:
        parent = openset.pop()

        rules = rules_per_depth.get(parent.depth, data.get_rules().values())
        assignments = _get_all_assignments(parent.state, rules=rules, partial=allow_partial_match, constrained_types=exceptions, backward=backward)
        if rng is not None:
            rng.shuffle(assignments)

        for rule, mapping in assignments:
            child = _try_instantiation(rule, mapping, parent, allow_parallel_chains, max_types_counts, backward)
            if child:
                child.set_parent(parent)
                parent.children.append(child)

        if len(parent.children) == 0:
            yield parent.get_path()

        if parent.depth + 1 < max_depth:
            openset += parent.children[::-1]
        else:
            for child in parent.children:
                yield child.get_path()


def get_chains(state, max_depth=1, allow_parallel_chains=False, allow_partial_match=False,
                   exceptions=[], max_types_counts=None, rules_per_depth={}, backward=False):
    root = ActionTree(state)
    for _ in _get_chains(state, root, max_depth, allow_parallel_chains, allow_partial_match,
                             exceptions=exceptions, max_types_counts=max_types_counts,
                             rules_per_depth=rules_per_depth, backward=backward):
        pass

    return root


def sample_quest(state, rng, max_depth, nb_retry=200,
                 allow_parallel_chains=False, allow_partial_match=False,
                 exceptions=[], max_types_counts=None,
                 rules_per_depth={}, backward=False):

    root = None
    chain_gen = _get_chains(state, root, max_depth, allow_parallel_chains, allow_partial_match, rng,
                                exceptions=exceptions, max_types_counts=max_types_counts,
                                rules_per_depth=rules_per_depth, backward=backward)

    best_chain = []
    for i, chain in enumerate(chain_gen):
        if i >= nb_retry:
            break

        if backward:
            chain = chain[::-1]

        # Chain shouldn't end with a navigation action unless it contains only navigation actions.
        # HACK: Because we don't generate quest using backward chaining yet,
        #       rstrip actions if navigation.
        if not all(_is_navigation(c.action) for c in chain):
            while _is_navigation(chain[-1].action):
                chain.pop()

        if len(chain) > len(best_chain):
            best_chain = chain

        if len(best_chain) >= max_depth:
            break

    return best_chain


def print_chains(chains, verbose=False, backward=False):
    for i, c in enumerate(chains):
        if backward:
            c = c[::-1]

        print("\n{}.\t{}".format(i + 1, c[0].action))
        for node in c[1:]:
            print("\t{}".format(node.action))
