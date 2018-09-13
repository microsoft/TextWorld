# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld import testing
from textworld.generator import data
from textworld.generator.chaining import ChainingOptions, get_chains
from textworld.logic import GameLogic, Proposition, State, Variable


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

    class Options(ChainingOptions):
        def get_rules(self, depth):
            return allowed_rules

    options = Options()
    options.max_depth = 5

    # No possible action since the wooden door is locked and
    # the player doesn't have the key.
    state = build_state(locked_door=True)
    chains = list(get_chains(state, options))
    assert len(chains) == 0

    # The door is now closed instead of locked.
    state = build_state(locked_door=False)
    chains = list(get_chains(state, options))
    assert len(chains) == 5

    # With more depth.
    state = build_state(locked_door=False)
    options.max_depth = 20
    chains = list(get_chains(state, options))
    assert len(chains) == 9


def test_applying_actions():
    state = build_state(locked_door=False)
    options = ChainingOptions()
    options.backward = True
    options.max_depth = 5
    chains = list(get_chains(state, options))

    expected_state = state
    for chain in chains:
        state = chain.initial_state.copy()
        for action in chain.actions:
            assert state.apply(action)

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

    options = ChainingOptions()
    options.backward = True
    options.max_depth = 3
    options.subquests = True
    options.create_variables = True
    options.rules_per_depth = [
        [data.get_rules()["take/c"], data.get_rules()["take/s"]],
        data.get_rules().get_matching("go.*"),
        [data.get_rules()["open/d"]],
    ]

    chains = list(get_chains(state, options))
    assert len(chains) == 18
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


def test_backward_chaining():
    P = Variable("P", "P")
    room = Variable("room", "r")
    kitchen = Variable("kitchen", "r")
    state = State([
        Proposition("at", [P, room]),
        Proposition("north_of", [kitchen, room]),
        Proposition("south_of", [room, kitchen]),
    ])

    options = ChainingOptions()
    options.backward = True
    options.max_depth = 2
    options.subquests = True
    options.create_variables = True
    options.rules_per_depth = [
        [data.get_rules()["take/c"], data.get_rules()["take/s"]],
        [data.get_rules()["open/c"]],
    ]
    options.restricted_types = {"d"}

    chains = list(get_chains(state, options))
    assert len(chains) == 3

    options = ChainingOptions()
    options.backward = True
    options.max_depth = 3
    options.subquests = True
    options.create_variables = True
    options.rules_per_depth = [
        [data.get_rules()["put"]],
        [data.get_rules()["go/north"]],
        [data.get_rules()["take/c"]],
    ]
    options.restricted_types = {"d"}

    chains = list(get_chains(state, options))
    assert len(chains) == 3


def test_parallel_quests():
    logic = GameLogic.parse("""
        type foo {
            rules {
                do_a :: not_a(foo) & $not_c(foo) -> a(foo);
                do_b :: not_b(foo) & $not_c(foo) -> b(foo);
                do_c :: $a(foo) & $b(foo) & not_c(foo) -> c(foo);
            }

            constraints {
                a_or_not_a :: a(foo) & not_a(foo) -> fail();
                b_or_not_b :: b(foo) & not_b(foo) -> fail();
                c_or_not_c :: c(foo) & not_c(foo) -> fail();
            }
        }
    """)

    state = State([
        Proposition.parse("a(foo)"),
        Proposition.parse("b(foo)"),
        Proposition.parse("c(foo)"),
    ])

    options = ChainingOptions()
    options.backward = True
    options.logic = logic

    options.max_depth = 3
    options.max_breadth = 1
    chains = list(get_chains(state, options))
    assert len(chains) == 2

    options.max_breadth = 2
    chains = list(get_chains(state, options))
    assert len(chains) == 3

    options.min_breadth = 2
    chains = list(get_chains(state, options))
    assert len(chains) == 1
    assert len(chains[0].actions) == 3
    assert chains[0].nodes[0].depth == 2
    assert chains[0].nodes[0].breadth == 2
    assert chains[0].nodes[0].parent == chains[0].nodes[2]
    assert chains[0].nodes[1].depth == 2
    assert chains[0].nodes[1].breadth == 1
    assert chains[0].nodes[1].parent == chains[0].nodes[2]
    assert chains[0].nodes[2].depth == 1
    assert chains[0].nodes[2].breadth == 1
    assert chains[0].nodes[2].parent == None

    options.min_breadth = 1
    options.create_variables = True
    chains = list(get_chains(State(), options))
    assert len(chains) == 5


def test_parallel_quests_navigation():
    logic = GameLogic.parse("""
        type P {
        }

        type I {
        }

        type r {
            rules {
                move :: at(P, r) & $free(r, r') -> at(P, r');
            }

            constraints {
                atat :: at(P, r) & at(P, r') -> fail();
            }
        }

        type o {
            rules {
                take :: $at(P, r) & at(o, r) -> in(o, I);
            }

            constraints {
                inat :: in(o, I) & at(o, r) -> fail();
            }
        }

        type flour : o {
        }

        type eggs : o {
        }

        type cake {
            rules {
                bake :: in(flour, I) & in(eggs, I) -> in(cake, I) & in(flour, cake) & in(eggs, cake);
            }

            constraints {
                inincake :: in(o, I) & in(o, cake) -> fail();
                atincake :: at(o, r) & in(o, cake) -> fail();
            }
        }
    """)

    state = State([
        Proposition.parse("at(P, r3: r)"),
        Proposition.parse("free(r2: r, r3: r)"),
        Proposition.parse("free(r1: r, r2: r)"),
    ])

    bake = [logic.rules["bake"]]
    non_bake = [r for r in logic.rules.values() if r.name != "bake"]

    options = ChainingOptions()
    options.backward = True
    options.create_variables = True
    options.min_depth = 3
    options.max_depth = 3
    options.min_breadth = 2
    options.max_breadth = 2
    options.logic = logic
    options.rules_per_depth = [bake, non_bake, non_bake]
    options.restricted_types = {"P", "r"}
    chains = list(get_chains(state, options))
    assert len(chains) == 2
