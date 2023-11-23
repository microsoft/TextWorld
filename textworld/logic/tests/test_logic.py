# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import pytest
from tatsu.exceptions import ParseError

from textworld.logic import Action, Rule
from textworld.logic import Variable, Placeholder
from textworld.logic import Proposition, Predicate, Signature
from textworld.logic import State, GameLogic
from textworld.generator import KnowledgeBase


def test_logic_parsing():
    P = Variable("P", "P")
    kitchen = Variable("kitchen", "r")
    egg = Variable("egg", "f")

    assert Variable.parse("P") == P
    assert Variable.parse("kitchen: r") == kitchen

    at_kitchen = Proposition("at", [P, kitchen])
    in_kitchen = Proposition("in", [egg, kitchen])
    raw_egg = Proposition("raw", [egg])
    cooked_egg = Proposition("cooked", [egg])

    assert Proposition.parse("at(P, kitchen: r)") == at_kitchen

    assert Signature.parse("at(P, r)") == at_kitchen.signature

    cook_egg = Action("cook", [at_kitchen, in_kitchen, raw_egg], [at_kitchen, in_kitchen, cooked_egg])
    assert Action.parse("cook :: $at(P, kitchen: r) & $in(egg: f, kitchen: r) & raw(egg: f) -> cooked(egg: f)") == cook_egg

    P = Placeholder("P", "P")
    r = Placeholder("r", "r")
    d = Placeholder("d", "d")
    rp = Placeholder("r'", "r")
    assert Placeholder.parse("P") == P
    assert Placeholder.parse("r") == r
    assert Placeholder.parse("d") == d
    assert Placeholder.parse("r'") == rp

    at_r = Predicate("at", [P, r])
    link = Predicate("link", [r, d, rp])
    unlocked = Predicate("unlocked", [d])
    at_rp = Predicate("at", [P, rp])
    assert Predicate.parse("link(r, d, r')") == link

    go = Rule("go", [at_r, link, unlocked], [link, unlocked, at_rp])
    assert Rule.parse("go :: at(P, r) & $link(r, d, r') & $unlocked(d) -> at(P, r')") == go

    # Make sure the types match in the whole expression
    with pytest.raises(ValueError):
        Rule.parse("take :: $at(P, r) & $in(c, r) & in(o: k, c) -> in(o, I)")

    query = Rule("query", [at_r, link, unlocked], [])
    assert Rule.parse_conjunctive_query("at(P, r) & link(r, d, r') & unlocked(d)") == query

    # Test negative prepositions and predicates.
    not_cooked_egg = Proposition("not_cooked", [egg])
    assert Proposition.parse("!cooked(egg: f)") == not_cooked_egg == cooked_egg.negate()

    locked = Predicate("locked", [d])
    not_locked = Predicate("not_locked", [d])
    assert Predicate.parse("!locked(d)") == not_locked == locked.negate()


def test_logic_parsing_eos():
    with pytest.raises(ParseError):
        Predicate.parse("at(P, r) & in(c, r)")


def test_state():
    state = State(KnowledgeBase.default().logic)

    P = Variable.parse("P")
    kitchen = Variable.parse("kitchen: r")
    study = Variable.parse("study: r")
    stove = Variable.parse("stove: o")
    at_kitchen = Proposition.parse("at(P, kitchen: r)")
    in_kitchen = Proposition.parse("in(stove: o, kitchen: r)")
    at_study = Proposition.parse("at(P, study: r)")

    assert not state.is_fact(at_kitchen)
    assert not state.is_fact(in_kitchen)
    assert not state.is_fact(at_study)
    assert len(state.variables) == 0
    assert len(state.variables_of_type("P")) == 0
    assert len(state.variables_of_type("r")) == 0
    assert len(state.variables_of_type("o")) == 0

    state.add_fact(at_kitchen)
    state.add_fact(in_kitchen)
    assert state.is_fact(at_kitchen)
    assert state.is_fact(in_kitchen)
    assert not state.is_fact(at_study)
    assert set(state.variables) == {P, kitchen, stove}
    assert state.variables_of_type("P") == {P}
    assert state.variables_of_type("r") == {kitchen}
    assert state.variables_of_type("o") == {stove}

    state.remove_fact(at_kitchen)
    assert not state.is_fact(at_kitchen)
    assert state.is_fact(in_kitchen)
    assert not state.is_fact(at_study)
    assert set(state.variables) == {kitchen, stove}
    assert len(state.variables_of_type("P")) == 0
    assert state.variables_of_type("r") == {kitchen}
    assert state.variables_of_type("o") == {stove}

    state.remove_fact(in_kitchen)
    assert not state.is_fact(at_kitchen)
    assert not state.is_fact(in_kitchen)
    assert not state.is_fact(at_study)
    assert len(state.variables) == 0
    assert len(state.variables_of_type("P")) == 0
    assert len(state.variables_of_type("r")) == 0
    assert len(state.variables_of_type("o")) == 0

    state.add_fact(at_study)
    assert not state.is_fact(at_kitchen)
    assert not state.is_fact(in_kitchen)
    assert state.is_fact(at_study)
    assert set(state.variables) == {P, study}
    assert state.variables_of_type("P") == {P}
    assert state.variables_of_type("r") == {study}
    assert len(state.variables_of_type("o")) == 0


def test_all_instantiations():
    state = State(KnowledgeBase.default().logic, [
        Proposition.parse("at(P, kitchen: r)"),
        Proposition.parse("in(key: o, kitchen: r)"),
        Proposition.parse("in(egg: o, kitchen: r)"),
        Proposition.parse("in(book: o, study: r)"),
        Proposition.parse("in(book: o, study: r)"),
        Proposition.parse("in(map: o, I)"),
    ])

    take = Rule.parse("take :: $at(P, r) & in(o, r) -> in(o, I)")
    actions = set(state.all_instantiations(take))
    assert actions == {
        Action.parse("take :: $at(P, kitchen: r) & in(key: o, kitchen: r) -> in(key: o, I)"),
        Action.parse("take :: $at(P, kitchen: r) & in(egg: o, kitchen: r) -> in(egg: o, I)"),
    }

    drop = take.inverse(name="drop")
    actions = set(state.all_instantiations(drop))
    assert actions == {
        Action.parse("drop :: $at(P, kitchen: r) & in(map: o, I) -> in(map: o, kitchen: r)"),
    }

    state.apply(*actions)
    actions = set(state.all_instantiations(drop))
    assert len(actions) == 0

    # The state is no longer aware of the I variable, so there are no solutions
    actions = set(state.all_instantiations(take))
    assert len(actions) == 0


def test_is_sequence_applicable():
    state = State(KnowledgeBase.default().logic, [
        Proposition.parse("at(P, r_1: r)"),
        Proposition.parse("empty(r_2: r)"),
        Proposition.parse("empty(r_3: r)"),
    ])

    assert state.is_sequence_applicable([
        Action.parse("go :: at(P, r_1: r) & empty(r_2: r) -> at(P, r_2: r) & empty(r_1: r)"),
        Action.parse("go :: at(P, r_2: r) & empty(r_3: r) -> at(P, r_3: r) & empty(r_2: r)"),
    ])

    assert not state.is_sequence_applicable([
        Action.parse("go :: at(P, r_1: r) & empty(r_2: r) -> at(P, r_2: r) & empty(r_1: r)"),
        Action.parse("go :: at(P, r_1: r) & empty(r_3: r) -> at(P, r_3: r) & empty(r_1: r)"),
    ])

    assert not state.is_sequence_applicable([
        Action.parse("go :: at(P, r_2: r) & empty(r_3: r) -> at(P, r_3: r) & empty(r_2: r)"),
        Action.parse("go :: at(P, r_3: r) & empty(r_1: r) -> at(P, r_1: r) & empty(r_3: r)"),
    ])


def test_match():
    rule = Rule.parse("go :: at(P, r) & $link(r, d, r') & $free(r, r') & $free(r', r) -> at(P, r')")

    mapping = {
        Placeholder.parse("P"): Variable.parse("P"),
        Placeholder.parse("r"): Variable.parse("r1: r"),
        Placeholder.parse("r'"): Variable.parse("r2: r"),
        Placeholder.parse("d"): Variable.parse("d"),
    }

    action = Action.parse("go :: at(P, r1: r) & $link(r1: r, d, r2: r)"
                          "      & $free(r1: r, r2: r) & $free(r2: r, r1: r) -> at(P, r2: r)")
    assert rule.match(action) == mapping

    # Order shouldn't matter
    action = Action.parse("go :: $link(r1: r, d, r2: r) & $free(r1: r, r2: r)"
                          "      & $free(r2: r, r1: r) & at(P, r1: r) -> at(P, r2: r)")
    assert rule.match(action) == mapping

    action = Action.parse("go :: at(P, r1: r) & $link(r1: r, d, r2: r)"
                          "      & $free(r2: r, r1: r) & $free(r1: r, r2: r) -> at(P, r2: r)")
    assert rule.match(action) == mapping

    # Predicate matches can't conflict
    action = Action.parse("go :: at(P, r1: r) & $link(r1: r, d, r2: r)"
                          "      & $free(r2: r, r1: r) & $free(r1: r, r2: r) -> at(P, r3: r)")
    assert rule.match(action) is None


def test_match_complex():
    rule = Rule.parse("combine/3 :: $at(P, r) & $correct_location(r) & $in(tool, I)"
                      "             & $in(tool', I) & $in(tool'', I) & in(o, I) & in(o', I)"
                      "             & in(o'', I) & $out(o''') & $used(slot) & used(slot') & used(slot'')"
                      "          -> in(o''', I) & free(slot') & free(slot'')")

    mapping = {
        Placeholder.parse("P"): Variable.parse("P"),
        Placeholder.parse("I"): Variable.parse("I"),
        Placeholder.parse("r"): Variable.parse("r"),
        Placeholder.parse("o"): Variable.parse("o1: o"),
        Placeholder.parse("o'"): Variable.parse("o2: o"),
        Placeholder.parse("o''"): Variable.parse("o3: o"),
        Placeholder.parse("o'''"): Variable.parse("o4: o"),
        Placeholder.parse("tool"): Variable.parse("tool1: tool"),
        Placeholder.parse("tool'"): Variable.parse("tool2: tool"),
        Placeholder.parse("tool''"): Variable.parse("tool3: tool"),
        Placeholder.parse("slot"): Variable.parse("slot1: slot"),
        Placeholder.parse("slot'"): Variable.parse("slot2: slot"),
        Placeholder.parse("slot''"): Variable.parse("slot3: slot"),
    }

    action = Action.parse("combine/3 :: $at(P, r) & $correct_location(r) & $in(tool1: tool, I)"
                          "             & $in(tool2: tool, I) & $in(tool3: tool, I) & in(o1: o, I)"
                          "             & in(o2: o, I) & in(o3: o, I) & $out(o4: o) & $used(slot1: slot)"
                          "             & used(slot2: slot) & used(slot3: slot)"
                          "          -> in(o4: o, I) & free(slot2: slot) & free(slot3: slot)")
    for _ in range(1000):
        assert rule.match(action) == mapping


def test_mementos_memoization():
    # Variable-free proposition.
    fact = Proposition("name")
    assert Proposition("name") is fact
    assert Proposition(name="name") is fact
    assert Proposition("name", []) is fact
    assert Proposition("name", arguments=[]) is fact
    assert Proposition(name="name", arguments=[]) is fact
    assert Proposition("name2") is not fact

    # General proposition.
    variables = [Variable("var_1"), Variable("var_2")]
    fact2 = Proposition("name", variables)
    assert fact2 is not fact
    assert Proposition("name", variables) is fact2
    assert Proposition("name", arguments=variables) is fact2
    assert Proposition(name="name", arguments=variables) is fact2
    assert Proposition("name2", variables) is not fact2

    assert Proposition("name", variables[:1]) is not fact2  # Missing a variable.
    assert Proposition("name", variables[::-1]) is not fact2  # Variable are reversed.

    # Type-free signature.
    sig = Signature("name")
    assert Signature("name") is sig
    assert Signature("name", []) is sig
    assert Signature("name", types=[]) is sig
    assert Signature(name="name", types=[]) is sig

    # General signature.
    types = ["type_A", "type_B"]
    sig2 = Signature("name", types)
    assert sig2 is not sig
    assert Signature("name", types) is sig2
    assert Signature("name", types=types) is sig2
    assert Signature(name="name", types=types) is sig2

    assert Signature("name", types[:1]) is not sig2  # Missing a variable.
    assert Signature("name", types[::-1]) is not sig2  # Variable are reversed.


def test_reverse_rule_and_action():
    logic = GameLogic.parse("""
        type container {
            predicates {
                open(container);
                closed(container);
            }

            rules {
                open  :: closed(container) -> open(container);
                close :: open(container) -> closed(container);
            }

            reverse_rules {
                open :: close;
            }

            inform7 {
                commands {
                    open :: "open {container}" :: "opening the {container}";
                    close :: "close {container}" :: "closing the {container}";
                }
            }

        }
    """)

    open_rule = logic.rules["open"]
    close_rule = logic.rules["close"]
    assert open_rule.reverse_rule == close_rule
    assert close_rule.reverse_rule == open_rule

    open_action = open_rule.instantiate({
        Placeholder("container", "container"): Variable("c_0", "container")
    })

    mapping = {"c_0": "chest"}
    assert open_action.format_command(mapping) == "open chest"
    r_open_action = open_action.inverse()
    assert r_open_action.name == "close"
    assert r_open_action.format_command(mapping) == "close chest"

    # Action's command template should persist through serialization.
    open_action2 = Action.deserialize(open_action.serialize())
    open_action2.format_command(mapping) == "open chest"

    assert open_action2.inverse() == r_open_action
