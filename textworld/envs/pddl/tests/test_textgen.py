import builtins
from pathlib import Path
from unittest.mock import Mock

import pytest

from textworld.generator.game import EntityInfo
from textworld.envs.pddl.logic import GameLogic
from textworld.envs.pddl.textgen import (
    ConditionalSymbol, EvalSymbol, ListSymbol, _parse_and_convert,
)


@pytest.fixture
def entity():
    info = EntityInfo("apple_1", "object")
    info.name = "apple"
    info.indefinite = "an"
    return info


def render(expression, **variables):
    return "".join(map(str, EvalSymbol(expression).derive({"variables": variables})))


@pytest.mark.parametrize("expression, expected", [
    ("o", "apple"),
    ("o.name", "apple"),
    ("o.id", "apple_1"),
    ("o.indefinite + ' ' + o.name", "an apple"),
    ("  (o.name or o.id)  ", "apple"),
    ("'  literal spaces  '", "  literal spaces  "),
    ("None", "None"),
    ("o.name or missing", "apple"),
    ("o or missing", "apple"),
])
def test_expression_rendering(entity, expression, expected):
    assert render(expression, o=entity) == expected


@pytest.mark.parametrize("name", [None, ""])
def test_optional_name_fallback(entity, name):
    entity.name = name
    assert render("o.name or o.id", o=entity) == "apple_1"
    assert render("o.name", o=entity) == str(name)
    if name is None:
        with pytest.raises(TypeError):
            render("o", o=entity)
    else:
        assert render("o", o=entity) == ""
    assert EvalSymbol("o or missing").derive({"variables": {"o": entity}})[0].symbol is entity


@pytest.mark.parametrize("field", EntityInfo.__slots__)
def test_public_entity_fields(entity, field):
    value = ["fruit", "food"] if field == "synonyms" else "display value"
    setattr(entity, field, value)
    assert render("o." + field, o=entity) == str(value)
    setattr(entity, field, None)
    assert render("o." + field, o=entity) == "None"


@pytest.mark.parametrize("expression", ["o + 'x'", "o.name + o.desc"])
def test_concatenation_keeps_type_errors(entity, expression):
    with pytest.raises(TypeError):
        render(expression, o=entity)


@pytest.mark.parametrize("name", ["missing", "self", "context", "json", "str", "__builtins__"])
def test_names_resolve_only_from_bindings(entity, name):
    with pytest.raises(NameError):
        render(name)
    assert render(name, **{name: entity}) == "apple"


@pytest.mark.parametrize("expression", [
    "grammar_sentinel()",
    "o.__class__",
    "o.name.__class__",
    "o.name.upper()",
    "o.synonyms[0]",
    "lambda: 'text'",
    "[x for x in o.synonyms]",
    "f'{o.name}'",
    "(x := 'text')",
    "'x' * 100",
    "o and o.name",
    "1",
])
def test_executable_and_unsupported_expressions_are_rejected(entity, monkeypatch, expression):
    sentinel = Mock()
    monkeypatch.setattr(builtins, "grammar_sentinel", sentinel, raising=False)
    with pytest.raises(SyntaxError):
        render(expression, o=entity)
    sentinel.assert_not_called()


def test_attributes_do_not_traverse_arbitrary_objects():
    value = Mock()
    with pytest.raises(TypeError):
        render("o.name", o=value)
    value.assert_not_called()


def test_bundled_expressions_keep_their_output(entity):
    source = Path(__file__).with_name("grammar.twl2").read_text()
    logic = GameLogic("", source)
    expressions = set()

    def collect(symbol):
        if isinstance(symbol, EvalSymbol):
            expressions.add(symbol.expression.strip())
        elif isinstance(symbol, ConditionalSymbol):
            collect(symbol.expression)
        elif isinstance(symbol, ListSymbol):
            collect(symbol.symbol)

    for rules in logic.grammar._rules.values():
        for rule in rules:
            for symbol in rule.rhs:
                collect(symbol)
    for action in logic.actions.values():
        for text in (action.template, action.feedback_rule):
            for symbol in _parse_and_convert(text, rule_name="symbols"):
                collect(symbol)

    expected = {
        "co": "apple", "co.name": "apple",
        "ko": "apple", "ko.name": "apple",
        "lend.name": "apple",
        "o": "apple", "o.name": "apple", "o.indefinite": "an",
        "o.indefinite + ' ' + o.name": "an apple",
        "o2.indefinite + ' ' + o2.name": "an apple",
        "outero": "apple", "outero.name": "apple",
        "outerr": "apple", "outerr.name": "apple",
        "r": "apple", "r.name": "apple", "r.indefinite": "an",
        "r.name or r.id": "apple",
    }
    variables = dict.fromkeys(("co", "ko", "lend", "o", "o2", "outero", "outerr", "r"), entity)
    for expression in expressions:
        assert render(expression, **variables) == expected[expression]
