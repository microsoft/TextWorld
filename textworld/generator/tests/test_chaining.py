# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld
from textworld.generator import data
from textworld.generator.chaining import ChainingOptions, get_chains
from textworld.logic import GameLogic, Proposition, State, Variable


def build_state(locked_door=False):
    # Set up a world with two rooms and a few objecs.
    M = textworld.GameMaker()
    bedroom = M.new_room("bedroom")
    kitchen = M.new_room("kitchen")
    rusty_key = M.new("k", name="rusty key")
    small_key = M.new("k", name="small key")
    chest = M.new("chest", name="chest")
    cabinet = M.new("chest", name="cabinet")
    robe = M.new("o", name="robe")
    path = M.connect(bedroom.south, kitchen.north)
    wooden_door = M.new_door(path, name="wooden door")

    M.set_player(bedroom)
    M.inventory.add(rusty_key)
    if locked_door:
        wooden_door.add_property("locked")
    else:
        wooden_door.add_property("closed")

    chest.add_property("locked")
    M.add_fact("match", rusty_key, chest)
    kitchen.add(chest)
    chest.add(small_key)

    M.add_fact("match", small_key, cabinet)
    cabinet.add_property("locked")
    bedroom.add(cabinet)
    cabinet.add(robe)

    return State(M.facts)


def test_chaining():
    # The following test depends on the available rules,
    # so instead of depending on what is in rules.txt,
    # we define the allowed_rules to used.
    allowed_rules = data.get_rules().get_matching(r"take\((o|k|f), (r|table|chest)\).*")
    allowed_rules += data.get_rules().get_matching(r"go\(.*\).*")
    allowed_rules += data.get_rules().get_matching(r"insert\((o|k|f), chest\).*", r"put\((o|k|f), table\).*")
    allowed_rules += data.get_rules().get_matching(r"open\((d|chest)\).*", r"close\((d|chest)\).*")
    allowed_rules += data.get_rules().get_matching(r"lock\((d|chest), k\).*", r"unlock\((d|chest), k\).*")
    allowed_rules += data.get_rules().get_matching(r"eat\(f\).*")

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
    # open/d > go/south > unlock/c > open/c > take/c-P-r-c-k-I
    # open/d > go/south > unlock/c > open/c > insert-P-r-c-k-I
    # open/d > go/south > unlock/c > open/c > go/north
    # open/d > go/south > unlock/c > go/north
    # open/d > go/south > close/d

    # With more depth.
    state = build_state(locked_door=False)
    options.max_depth = 20
    chains = list(get_chains(state, options))
    assert len(chains) == 9
    # open/d > go/south > unlock/c > open/c > take/c-P-r-c-k-I > go/north > unlock/c > open/c > take/c > go/south > insert > go/north
    # open/d > go/south > unlock/c > open/c > take/c-P-r-c-k-I > go/north > unlock/c > open/c > insert-P-r-c-k-I > go/south
    # open/d > go/south > unlock/c > open/c > take/c-P-r-c-k-I > go/north > unlock/c > open/c > insert-P-r-c-k-I > go/south
    # open/d > go/south > unlock/c > open/c > take/c-P-r-c-k-I > go/north > unlock/c > open/c > go/south
    # open/d > go/south > unlock/c > open/c > take/c-P-r-c-k-I > go/north > unlock/c > go/south
    # open/d > go/south > unlock/c > open/c > insert-P-r-c-k-I > go/north
    # open/d > go/south > unlock/c > open/c > go/north
    # open/d > go/south > unlock/c > go/north
    # open/d > go/south > close/d


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
        data.get_rules().get_matching(r"take\(o, chest\).*", r"take\(o, table\).*"),
        data.get_rules().get_matching(r"go\(.*\).*"),
        data.get_rules().get_matching(r"open\(d\).*"),
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
        data.get_rules().get_matching(r"take\(o, chest\).*", r"take\(o, table\).*"),
        data.get_rules().get_matching(r"open\(chest\).*"),
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
        data.get_rules().get_matching(r"put\(o, table\).*"),
        data.get_rules().get_matching(r"go\(north\).*"),
        data.get_rules().get_matching(r"take\(o, chest\).*"),
    ]
    options.restricted_types = {"d"}

    chains = list(get_chains(state, options))
    assert len(chains) == 3


def test_parallel_quests():
    logic = GameLogic.parse("""
        type t { }
        type P { }
        type I { }

        type foo : t {
            predicates {
                not_a(foo);
                not_b(foo);
                not_c(foo);
                a(foo);
                b(foo);
                c(foo);
            }

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
            predicates {
                at(P, r);
                free(r, r);
            }

            rules {
                move :: at(P, r) & $free(r, r') -> at(P, r');
            }

            constraints {
                atat :: at(P, r) & at(P, r') -> fail();
            }
        }

        type t {
        }

        type o : t {
            predicates {
                at(o, r);
                in(o, I);
            }

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

        type cake : o {
            predicates {
                in(o, cake);
            }

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

    bake = [logic.rules["bake.0"]]
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
