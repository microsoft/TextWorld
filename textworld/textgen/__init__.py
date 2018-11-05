from tatsu.model import NodeWalker
from typing import Iterable, Optional, Tuple

from textworld.textgen.model import TextGrammarModelBuilderSemantics
from textworld.textgen.parser import TextGrammarParser


class Alternative:
    """
    A single alternative in a production rule.
    """

    def full_form(self, include_adj=True) -> str:
        adj, noun = self.split_form(include_adj)
        if adj is None:
            return noun
        else:
            return adj + "|" + noun


class LiteralAlternative(Alternative):
    """
    An alternative from a literal string.
    """

    def __init__(self, value: str):
        self._value = value

    def split_form(self, include_adj=True) -> Tuple[Optional[str], str]:
        return None, self._value


class AdjectiveNounAlternative(Alternative):
    """
    An alternative that specifies an adjective and a noun.
    """

    def __init__(self, adjective: str, noun: str):
        self._adjective = adjective
        self._noun = noun

    def split_form(self, include_adj=True) -> Tuple[Optional[str], str]:
        if include_adj:
            return self._adjective, self._noun
        else:
            return None, self._noun


class MatchAlternative(Alternative):
    """
    An alternative that specifies matching names for two objects.
    """

    def __init__(self, lhs: Alternative, rhs: Alternative):
        self.lhs = lhs
        self.rhs = rhs

    def full_form(self, include_adj=True) -> str:
        return self.lhs.full_form(include_adj) + " <-> " + self.rhs.full_form(include_adj)


class ProductionRule:
    """
    A production rule in a text grammar.
    """

    def __init__(self, symbol: str, alternatives: Iterable[Alternative]):
        self.symbol = symbol
        self.alternatives = tuple(alternatives)


class _Converter(NodeWalker):
    def walk_list(self, node):
        return [self.walk(child) for child in node]

    def walk_str(self, node):
        return node.replace("\\n", "\n")

    def walk_Literal(self, node):
        value = self.walk(node.value)
        if value:
            return LiteralAlternative(value)
        else:
            # Skip empty literals
            return None

    def walk_AdjectiveNoun(self, node):
        return AdjectiveNounAlternative(self.walk(node.adjective), self.walk(node.noun))

    def walk_Match(self, node):
        return MatchAlternative(self.walk(node.lhs), self.walk(node.rhs))

    def walk_ProductionRule(self, node):
        alts = [alt for alt in self.walk(node.alternatives) if alt is not None]
        return ProductionRule(node.symbol, alts)

    def walk_TextGrammar(self, node):
        return TextGrammar(self.walk(node.rules))


class TextGrammar:
    _PARSER = TextGrammarParser(semantics=TextGrammarModelBuilderSemantics(), parseinfo=True)
    _CONVERTER = _Converter()

    def __init__(self, rules: Iterable[ProductionRule]):
        self.rules = {rule.symbol: rule for rule in rules}

    @classmethod
    def parse(cls, grammar: str, filename: Optional[str] = None):
        model = cls._PARSER.parse(grammar, filename=filename)
        return cls._CONVERTER.walk(model)
