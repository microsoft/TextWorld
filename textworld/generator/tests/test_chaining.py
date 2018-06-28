# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld import testing
from textworld.generator import data
from textworld.logic import Proposition, State, Variable

from textworld.generator import chaining


# noinspection PyPep8Naming
def build_state(locked_door=False):
    # Set up a world with two rooms and a few objecs.
    P = Variable("P")
    I = Variable("I")
    bedroom = Variable("bedroom", "r")
    kitchen = Variable("kitchen", "r")
    rusty_key = Variable("rusty key", "k")
    small_key = Variable("small key", "k")
    wooden_door = Variable("wooden door", "d")
    chest = Variable("chest", "c")
    cabinet = Variable("cabinet", "c")
    robe = Variable("robe", "o")

    state = State([
        Proposition("at", [P, bedroom]),
        Proposition("south_of", [kitchen, bedroom]),
        Proposition("north_of", [bedroom, kitchen]),
        Proposition("link", [bedroom, wooden_door, kitchen]),
        Proposition("link", [kitchen, wooden_door, bedroom]),

        Proposition("locked" if locked_door else "closed", [wooden_door]),

        Proposition("in", [rusty_key, I]),
        Proposition("match", [rusty_key, chest]),
        Proposition("locked", [chest]),
        Proposition("at", [chest, kitchen]),
        Proposition("in", [small_key, chest]),

        Proposition("match", [small_key, cabinet]),
        Proposition("locked", [cabinet]),
        Proposition("at", [cabinet, bedroom]),
        Proposition("in", [robe, cabinet]),
    ])

    return state


def test_chaining():
    # The following test depends on the available rules,
    # so instead of depending on what is in rules.txt,
    # we define the allowed_rules to used.
    allowed_rules = data.get_rules().get_matching("take/.*")
    allowed_rules += data.get_rules().get_matching("go.*")
    allowed_rules += data.get_rules().get_matching("insert.*", "put.*")
    allowed_rules += data.get_rules().get_matching("open.*", "close.*")
    allowed_rules += data.get_rules().get_matching("lock.*", "unlock.*")
    allowed_rules += data.get_rules().get_matching("eat.*")

    # No possible action since the wooden door is locked and
    # the player doesn't have the key.
    state = build_state(locked_door=True)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())
    assert len(chains) == 0

    # The door is now closed instead of locked.
    state = build_state(locked_door=False)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())
    # chaining.print_chains(chains)
    assert len(chains) == 5

    # With more depth.
    state = build_state(locked_door=False)
    tree = chaining.get_chains(state, max_depth=20,
                               rules_per_depth={i: allowed_rules for i in range(20)})
    chains = list(tree.traverse_preorder())
    assert len(chains) == 9


def test_to_networkx():
    # Below copied from test_chaining()
    allowed_rules = data.get_rules().get_matching("take/.*")
    allowed_rules += data.get_rules().get_matching("go.*")
    allowed_rules += data.get_rules().get_matching("insert.*", "put.*")
    allowed_rules += data.get_rules().get_matching("open.*", "close.*")
    allowed_rules += data.get_rules().get_matching("lock.*", "unlock.*")
    allowed_rules += data.get_rules().get_matching("eat.*")

    # No possible action since the wooden door is locked and
    # the player doesn't have the key.
    state = build_state(locked_door=True)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())
    assert len(chains) == 0

    # The door is now closed instead of locked.
    state = build_state(locked_door=False)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    G, labels = tree.to_networkx()
    assert G is not None
    assert labels is not None
    assert len(labels) > 0


def test_print_chains():
    from textworld.generator import print_chains

    allowed_rules = data.get_rules().get_matching("take/.*")
    allowed_rules += data.get_rules().get_matching("go.*")
    allowed_rules += data.get_rules().get_matching("insert.*", "put.*")
    allowed_rules += data.get_rules().get_matching("open.*", "close.*")
    allowed_rules += data.get_rules().get_matching("lock.*", "unlock.*")
    allowed_rules += data.get_rules().get_matching("eat.*")

    # No possible action since the wooden door is locked and
    # the player doesn't have the key.
    state = build_state(locked_door=True)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())
    assert len(chains) == 0

    # The door is now closed instead of locked.
    state = build_state(locked_door=False)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())

    # Only validates that printing chains does not raise exception.
    with testing.capture_stdout() as stdout:
        print_chains(chains, backward=True)
        stdout.seek(0)
        assert len(stdout.read()) > 0


def test_print_chains_backwards():
    from textworld.generator import print_chains

    allowed_rules = data.get_rules().get_matching("take/.*")
    allowed_rules += data.get_rules().get_matching("go.*")
    allowed_rules += data.get_rules().get_matching("insert.*", "put.*")
    allowed_rules += data.get_rules().get_matching("open.*", "close.*")
    allowed_rules += data.get_rules().get_matching("lock.*", "unlock.*")
    allowed_rules += data.get_rules().get_matching("eat.*")

    # No possible action since the wooden door is locked and
    # the player doesn't have the key.
    state = build_state(locked_door=True)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())
    assert len(chains) == 0

    # The door is now closed instead of locked.
    state = build_state(locked_door=False)
    tree = chaining.get_chains(state, max_depth=5,
                               rules_per_depth={i: allowed_rules for i in range(5)})
    chains = list(tree.traverse_preorder())

    # Only validates that printing chains does not raise exception.
    with testing.capture_stdout() as stdout:
        print_chains(chains, backward=True)
        stdout.seek(0)
        assert len(stdout.read()) > 0


def test_reversing_action():
    state = build_state(locked_door=False)
    tree = chaining.get_chains(state, max_depth=5)
    chains = list(tree.traverse_preorder())

    expected_state = state
    for chain in chains:
        state = chain[-1].state.copy()
        for node in chain[0:][::-1]:
            action = node.action
            assert state.apply(action.inverse())
            assert chaining.check_state(state)

        assert expected_state == state


def test_going_through_door():
    P = Variable("P", "P")
    room = Variable("room", "r")
    kitchen = Variable("kitchen", "r")
    state = State()
    state.add_facts([
        Proposition("at", [P, room]),
        Proposition("north_of", [kitchen, room]),
        Proposition("free", [kitchen, room]),
        Proposition("free", [room, kitchen]),
        Proposition("south_of", [room, kitchen])
    ])

    # Sample quests.
    chains = []
    rules_per_depth = {0: [data.get_rules()["take/c"], data.get_rules()["take/s"]],
                       1: data.get_rules().get_matching("go.*"),
                       2: [data.get_rules()["open/d"]]}
    tree_of_possible = chaining.get_chains(state,
                                           max_depth=3,
                                           allow_partial_match=True,
                                           exceptions=[],
                                           rules_per_depth=rules_per_depth,
                                           backward=True)
    chains = list(tree_of_possible.traverse_preorder(subquests=True))
    # chaining.print_chains(chains)
    # 1. take/c(P, room, c_0, o_0, I)
    # 2. take/c(P, room, c_0, o_0, I) -> go/north(P, r_0, room)
    # 3. take/c(P, room, c_0, o_0, I) -> go/north(P, r_0, room) -> open/d(P, r_0, d_0, room)
    # 4. take/c(P, room, c_0, o_0, I) -> go/south(P, kitchen, room)
    # 5. take/c(P, room, c_0, o_0, I) -> go/south(P, kitchen, room) -> open/d(P, kitchen, d_0, room)
    # 6. take/c(P, room, c_0, o_0, I) -> go/east(P, r_0, room)
    # 7. take/c(P, room, c_0, o_0, I) -> go/east(P, r_0, room) -> open/d(P, r_0, d_0, room)
    # 8. take/c(P, room, c_0, o_0, I) -> go/west(P, r_0, room)
    # 9. take/c(P, room, c_0, o_0, I) -> go/west(P, r_0, room) -> open/d(P, r_0, d_0, room)
    # 10. take/s(P, room, s_0, o_0, I)
    # 11. take/s(P, room, s_0, o_0, I) -> go/north(P, r_0, room)
    # 12. take/s(P, room, s_0, o_0, I) -> go/north(P, r_0, room) -> open/d(P, r_0, d_0, room)
    # 13. take/s(P, room, s_0, o_0, I) -> go/south(P, kitchen, room)
    # 14. take/s(P, room, s_0, o_0, I) -> go/south(P, kitchen, room) -> open/d(P, kitchen, d_0, room)
    # 15. take/s(P, room, s_0, o_0, I) -> go/east(P, r_0, room)
    # 16. take/s(P, room, s_0, o_0, I) -> go/east(P, r_0, room) -> open/d(P, r_0, d_0, room)
    # 17. take/s(P, room, s_0, o_0, I) -> go/west(P, r_0, room)
    # 18. take/s(P, room, s_0, o_0, I) -> go/west(P, r_0, room) -> open/d(P, r_0, d_0, room)
    assert len(chains) == 18


def test_backward_chaining():
    P = Variable("P", "P")
    room = Variable("room", "r")
    kitchen = Variable("kitchen", "r")
    state = State([
        Proposition("at", [P, room]),
        Proposition("north_of", [kitchen, room]),
        Proposition("south_of", [room, kitchen]),
    ])

    rules_per_depth = {0: [data.get_rules()["take/c"], data.get_rules()["take/s"]],
                       1: [data.get_rules()["open/c"]]}

    tree_of_possible = chaining.get_chains(state,
                                           max_depth=2,
                                           allow_partial_match=True,
                                           exceptions=['d'],
                                           rules_per_depth=rules_per_depth,
                                           backward=True)

    chains = list(tree_of_possible.traverse_preorder(subquests=True))
    assert len(chains) == 3
    for chain in chains:
        for depth, action in enumerate(chain):
            assert action.action.name in [rule.name for rule in rules_per_depth[depth]]

    rules_per_depth = {0: [data.get_rules()["put"]],
                       1: [data.get_rules()["go/north"]],
                       2: [data.get_rules()["take/c"]]}

    tree_of_possible = chaining.get_chains(state,
                                           max_depth=3,
                                           allow_partial_match=True,
                                           exceptions=['d'],
                                           rules_per_depth=rules_per_depth,
                                           backward=True)

    chains = list(tree_of_possible.traverse_preorder(subquests=True))
    assert len(chains) == 3
    for chain in chains:
        for depth, action in enumerate(chain):
            assert action.action.name in [rule.name for rule in rules_per_depth[depth]]
