from tatsu.model import NodeWalker
from typing import Iterable, Optional, Tuple, List

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


class LiteralChunk:
    """
    It creates an object with a [str] value for every single literal.
    literal is defined as any string which is not a symbol, i.e. it is not bounded by hashtags.
    """
    def __init__(self,  value: str):
        self._value = value


class SymbolChunk:
    """
    It creates an object with a [str] value for every single symbol.
    symbol is defined as any string in between two consecutive hashtags, e.g. #it_is_a_symbol#.
    """
    def __init__(self,  value: str):
        self._value = value


class LiteralAlternative(Alternative):
    """
        An alternative from a literal string and represents it as a chunk of literal and symbol objects.
    """
    def __init__(self, node: str):
        self._node = node
        # self._val_chunk contains the objects which make the string.
        # It is equivalent to self._value in LiteralAlternative.
        self._val_chunk = self._symbol_finder(self._node)

    def _symbol_finder(self, node):
        self.chunks = []
        while node:
            is_has_tag = [i for i, ltr in enumerate(node) if ltr == '#']
            if is_has_tag:
                if node[:is_has_tag[0]]:
                    self.chunks.append(LiteralChunk(node[:is_has_tag[0]]))
                    self.chunks.append(SymbolChunk(node[is_has_tag[0]:is_has_tag[1] + 1]))
                else:
                    self.chunks.append(SymbolChunk(node[is_has_tag[0]:is_has_tag[1] + 1]))

                node = node[is_has_tag[1] + 1:]
            else:
                if node:
                    self.chunks.append(LiteralChunk(node))
                break
        return self.chunks

    def split_form(self, include_adj=True) -> Tuple[Optional[str], str]:
        return None, self._node


class AdjectiveNounAlternative(LiteralAlternative):
    """
    An alternative that specifies an adjective and a noun.
    """

    def __init__(self, adj_node: str, n_node: str):
        self._adj_node = adj_node
        self._n_node = n_node
        # self._adj_chunk contains the objects which make the adjective string.
        # self._noun_chunk contains the objects which make the noun string.
        # These are equivalent to self._adjective and self._noun in AdjectiveNounAlternative.
        self._adj_chunk = self._symbol_finder(self._adj_node)
        self._noun_chunk = self._symbol_finder(self._n_node)

    def split_form(self, include_adj=True) -> Tuple[Optional[str], str]:
        if include_adj:
            return self._adj_node, self._n_node
        else:
            return None, self._n_node


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
