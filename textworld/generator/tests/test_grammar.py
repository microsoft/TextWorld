# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld.generator.data import KnowledgeBase
from textworld.generator.vtypes import NotEnoughNounsError, get_new
from textworld.logic import Action, Placeholder, Proposition, Rule, State, Variable


P = Variable("P", "P")
I = Variable("I", "I")
bedroom = Variable("bedroom", "r")
kitchen = Variable("kitchen", "r")
old_key = Variable("old key", "k")
rusty_key = Variable("rusty key", "k")
small_key = Variable("small key", "k")
wooden_door = Variable("wooden door", "d")
glass_door = Variable("glass door", "d")
chest = Variable("chest", "c")
cabinet = Variable("cabinet", "c")
counter = Variable("counter", "s")
robe = Variable("robe", "o")


def maybe_instantiate_variables(rule, mapping, state, max_types_counts=None):
    types_counts = KnowledgeBase.default().types.count(state)

    # Instantiate variables if needed
    try:
        for ph in rule.placeholders:
            if mapping.get(ph) is None:
                name = get_new(ph.type, types_counts, max_types_counts)
                mapping[ph] = Variable(name, ph.type)
    except NotEnoughNounsError:
        return None

    return rule.instantiate(mapping)


def build_state(door_state="open"):
    # Set up a world with two rooms and a few objecs.
    state = State(KnowledgeBase.default().logic, [
        Proposition("at", [P, bedroom]),
        Proposition("south_of", [kitchen, bedroom]),
        Proposition("north_of", [bedroom, kitchen]),
        Proposition("link", [bedroom, wooden_door, kitchen]),
        Proposition("link", [kitchen, wooden_door, bedroom]),
        Proposition(door_state, [wooden_door]),
        #
        Proposition("in", [rusty_key, I]),
        Proposition("match", [rusty_key, chest]),
        Proposition("locked", [chest]),
        Proposition("at", [chest, kitchen]),
        Proposition("in", [small_key, chest]),
        #
        Proposition("match", [small_key, cabinet]),
        Proposition("locked", [cabinet]),
        Proposition("at", [cabinet, bedroom]),
        Proposition("in", [robe, cabinet]),
    ])
    return state


def test_variables():
    for var in [P, bedroom, robe, counter, chest]:
        data = var.serialize()
        loaded_var = Variable.deserialize(data)
        assert loaded_var == var


def test_propositions():
    state = build_state()
    for prop in state.facts:
        data = prop.serialize()
        loaded_prop = Proposition.deserialize(data)
        assert loaded_prop == prop


def test_rules():
    for rule in KnowledgeBase.default().rules.values():
        infos = rule.serialize()
        loaded_rule = Rule.deserialize(infos)
        assert loaded_rule == rule


def test_get_reverse_action():
    kb = KnowledgeBase.default()
    for rule in kb.rules.values():
        empty_state = State(KnowledgeBase.default().logic)
        action = maybe_instantiate_variables(rule, kb.types.constants_mapping.copy(), empty_state)
        r_action = kb.get_reverse_action(action)

        if rule.name.startswith("eat"):
            assert r_action is None
        else:
            assert r_action is not None

            # Check if that when applying the reverse rule we can re-obtain
            # the previous state.
            state = State(KnowledgeBase.default().logic, action.preconditions)

            new_state = state.copy()
            assert new_state.apply(action)

            r_state = new_state.copy()
            r_state.apply(r_action)
            assert state == r_state


def test_serialization_deserialization():
    rule = KnowledgeBase.default().rules["go/east"]
    mapping = {
        Placeholder("r'"): Variable("room1", "r"),
        Placeholder("r"): Variable("room2"),
    }
    mapping.update(KnowledgeBase.default().types.constants_mapping)
    action = rule.instantiate(mapping)
    infos = action.serialize()
    action2 = Action.deserialize(infos)
    assert action == action2
