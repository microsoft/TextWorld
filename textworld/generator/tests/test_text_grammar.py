# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import json
import unittest

from textworld.generator.text_grammar import Grammar
from textworld.generator.text_grammar import GrammarOptions


class ContainsEveryObjectContainer:
    def __contains__(self, item):
        return True


class TestGrammarOptions(unittest.TestCase):
    def test_serialization(self):
        options = GrammarOptions(theme="dummy", include_adj=True, names_to_exclude=["name1", "name1", "name2"])
        data = options.serialize()
        json_data = json.dumps(data)
        options2 = GrammarOptions.deserialize(json.loads(json_data))
        assert options == options2


class GrammarTest(unittest.TestCase):
    def test_grammar_eq(self):
        grammar = Grammar()
        grammar2 = Grammar()
        self.assertEqual(grammar, grammar2, "Testing two grammar files are equivalent")

    def test_grammar_eq2(self):
        grammar = Grammar(options={'theme': 'house'})
        grammar2 = Grammar(options={'theme': 'basic'})
        self.assertNotEqual(grammar, grammar2, "Testing two different grammar files are not equal")

    def test_grammar_get_random_expansion_fail(self):
        """
        Tests failure when getting a non-existent flag
        (unsuccess used in names as _fail is a special flag in nosetests)
        """
        grammar = Grammar()
        bad_tag_name = 'fahawagads'
        try:
            grammar.get_random_expansion(tag=bad_tag_name)
            self.assertTrue(False, "We should have errored with a value error about a non-existent tag")
        except ValueError as e:
            self.assertTrue(bad_tag_name in str(e), "Tag name does not occur in error message")

    def split_name_adj_noun_fail(self):
        """
        What happens if we have too many separators?
        """
        grammar = Grammar()
        try:
            grammar.split_name_adj_noun('A|B|C', True)
            self.assertTrue(False, "We should have errored about too many separators")
        except ValueError:
            pass

    def generate_name_fail(self):
        grammar = Grammar()
        try:
            grammar.generate_name('object', 'vault', False, exclude=ContainsEveryObjectContainer())
            self.assertTrue(False, "We should have errored about an impossible object name")
        except ValueError:
            pass

    def generate_name_force_numbered(self):
        suffix = '_1'

        grammar = Grammar(options={'allowed_variables_numbering': True})
        name, adj, noun = grammar.generate_name('object', 'vault', False, exclude=ContainsEveryObjectContainer())
        self.assertTrue(name.endswith(suffix), 'Checking name ends with suffix')
        self.assertTrue(adj.endswith(suffix), 'Checking adj ends with suffix')
        self.assertTrue(noun.endswith(suffix), 'Checking noun ends with suffix')

    def test_get_all_expansions_for_tag_not_existing(self):
        grammar = Grammar()
        result = grammar.get_all_expansions_for_tag('fahawagads')
        self.assertEqual(len(result), 0, 'Result is not empty')

    def test_get_all_expansions_for_tag(self):
        grammar = Grammar()
        result = grammar.get_all_expansions_for_tag('#clean_(r)#')
        self.assertNotEqual(len(result), 0, 'No expansions for library tag found')

    def test_get_all_expansions_for_type(self):
        grammar = Grammar()
        result = grammar.get_all_expansions_for_type('d')
        self.assertNotEqual(len(result), 0, 'No expansions for door type found')

    def test_get_all_names_for_type(self):
        grammar = Grammar()
        result = grammar.get_all_names_for_type('d', False)
        self.assertNotEqual(len(result), 0, 'No names for door type found')

    def test_get_all_adj_for_type(self):
        grammar = Grammar()
        result = grammar.get_all_adjective_for_type('d')
        self.assertNotEqual(len(result), 0, 'No adjectives for door type found')

    def test_get_all_nouns_for_type(self):
        grammar = Grammar()
        result = grammar.get_all_nouns_for_type('d')
        self.assertNotEqual(len(result), 0, 'No nouns for door type found')
