# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import re
import warnings
from os.path import join as pjoin
from collections import OrderedDict, defaultdict
from typing import Optional, Mapping, List, Tuple, Container

from numpy.random import RandomState

import textworld
from textworld import g_rng
from textworld.utils import uniquify
from textworld.generator import data


NB_EXPANSION_RETRIES = 20


def fix_determinant(var):
    var = var.replace("  ", " ")
    var = var.replace(" a a", " an a")
    var = var.replace(" a e", " an e")
    var = var.replace(" a i", " an i")
    var = var.replace(" a o", " an o")
    var = var.replace(" a u", " an u")
    var = var.replace(" A a", " An a")
    var = var.replace(" A e", " An e")
    var = var.replace(" A i", " An i")
    var = var.replace(" A o", " An o")
    var = var.replace(" A u", " An u")
    return var


class GrammarFlags:
    __slots__ = ['theme', 'include_adj', 'blend_descriptions',
                 'ambiguous_instructions', 'only_last_action',
                 'blend_instructions',
                 'allowed_variables_numbering', 'unique_expansion']

    def __init__(self, flags=None, **kwargs):
        flags = flags or kwargs

        self.theme = flags.get("theme", "house")
        self.allowed_variables_numbering = flags.get("allowed_variables_numbering", False)
        self.unique_expansion = flags.get("unique_expansion", False)
        self.include_adj = flags.get("include_adj", False)
        self.only_last_action = flags.get("only_last_action", False)
        self.blend_instructions = flags.get("blend_instructions", False)
        self.blend_descriptions = flags.get("blend_descriptions", False)
        self.ambiguous_instructions = flags.get("ambiguous_instructions", False)

    def encode(self):
        """ Generate UUID for this set of grammar flags.
        """
        values = [int(getattr(self, s)) for s in self.__slots__[1:]]
        flag = "".join(map(str, values))

        from hashids import Hashids
        hashids = Hashids(salt="TextWorld")
        return self.theme + "-" + hashids.encode(int(flag))


def encode_flags(flags):
    return GrammarFlags(flags).encode()


class Grammar:
    """
    Context-Free Grammar for text generation.
    """

    def __init__(self, flags: Mapping = {}, rng: Optional[RandomState] = None):
        """
        Create a grammar.

        :param flags:
            Flags guiding the text generation process.
            TODO: describe expected flags.
        :param rng:
            Random generator used for sampling tag expansions.
        """
        self.flags = flags
        self.grammar = OrderedDict()
        self.rng = g_rng.next() if rng is None else rng
        self.allowed_variables_numbering = self.flags.get("allowed_variables_numbering", False)
        self.unique_expansion = self.flags.get("unique_expansion", False)
        self.all_expansions = defaultdict(list)

        # The current used symbols
        self.overflow_dict = OrderedDict()
        self.used_names = set(self.flags.get("names_to_exclude", []))

        # Load the grammar associated to the provided theme.
        self.theme = self.flags.get("theme", "house")
        grammar_contents = []

        # Load the object names file
        files = os.listdir(data.get_text_grammars_path())
        files = [f for f in files if f.startswith(self.theme + "_") and f.endswith(".twg")]
        for filename in files:
            with open(pjoin(data.get_text_grammars_path(), filename)) as f:
                grammar_contents.extend(f.readlines())

        self._parse(grammar_contents)

    def __eq__(self, other):
        return (isinstance(other, Grammar) and
                self.overflow_dict == other.overflow_dict and
                self.grammar == other.grammar and
                self.flags == other.flags and
                self.used_names == other.used_names)

    def _parse(self, lines: List[str]):
        """
        Parse lines and add them to the grammar.
        """
        for line in lines:
            if not line.startswith("#") and line.strip() != "":
                line = line.strip()
                line = line.replace("\\n", "\n")
                symbol = "#" + line.split(":")[0] + "#"
                tokens = line.split(":", 1)[1].split(";")

                # Remove empty tokens
                for token in tokens:
                    if token == "":
                        tokens.remove(token)

                if symbol not in self.grammar:
                    self.grammar[symbol] = []

                self.grammar[symbol].extend(tokens)

        for k, v in self.grammar.items():
            self.grammar[k] = tuple(v)

    def has_tag(self, tag: str) -> bool:
        """
        Check if the grammar has a given tag.
        """
        return tag in self.grammar

    def get_random_expansion(self, tag: str, rng: Optional[RandomState] = None) -> str:
        """
        Return a randomly chosen expansion for the given tag.

        Parameters
        ----------
        tag :
            Grammar tag to be expanded.
        rng : optional
            Random generator used to chose an expansion when there is many.
            By default, it used the random generator of this grammar object.

        Returns
        -------
        expansion :
            An expansion chosen randomly for the provided tag.
        """
        rng = rng or self.rng

        if not self.has_tag(tag):
            raise ValueError("Tag: {} does not exist!".format(tag))

        for _ in range(NB_EXPANSION_RETRIES):
            expansion = rng.choice(self.grammar[tag])
            if not self.unique_expansion or expansion not in self.all_expansions[tag]:
                break

        self.all_expansions[tag].append(expansion)
        return expansion


    def expand(self, text: str, rng: Optional[RandomState] = None) -> str:
        """
        Expand some text until there is no more tag to expand.

        Parameters
        ----------
        text :
            Text potentially containing grammar tags to be expanded.
        rng : optional
            Random generator used to chose an expansion when there is many.
            By default, it used the random generator of this grammar object.

        Returns
        -------
        expanded_text :
            Resulting text in which there is no grammar tag left to be expanded.
        """
        rng = self.rng if rng is None else rng
        while "#" in text:
            to_replace = re.findall(r'[#][^#]*[#]', text)
            tag = self.rng.choice(to_replace)
            replacement = self.get_random_expansion(tag, rng)
            text = text.replace(tag, replacement)

        return text

    def split_name_adj_noun(self, candidate: str, include_adj: bool) -> Optional[Tuple[str, str, str]]:
        """
        Extract the full name, the adjective and the noun from a string.

        Parameters
        ----------
        candidate :
            String that may contain one adjective-noun sperator '|'.
        include_adj : optional
            If True, the name can contain a generated adjective.
            If False, any generated adjective will be discarded.

        Returns
        -------
        name :
            The whole name, i.e. `adj + " " + noun`.
        adj :
            The adjective part of the name.
        noun :
            The noun part of the name.
        """
        parts = candidate.split("|")
        noun = parts[-1].strip()
        if len(parts) == 1 or not include_adj:
            adj = None
        elif len(parts) == 2:
            adj = parts[0].strip()
        else:
            raise ValueError("Too many separators '|' in '{}'".format(candidate))

        name = adj + " " + noun if adj is not None else noun
        return name, adj, noun

    def generate_name(self, obj_type: str, room_type: str = "",
                      include_adj: bool = True, exclude: Container[str] = []) -> Tuple[str, str, str]:
        """
        Generate a name given an object type and the type room it belongs to.

        Parameters
        ----------
        obj_type :
            Type of the object for which we will generate a name.
        room_type : optional
            Type of the room the object belongs to.
        include_adj : optional
            If True, the name can contain a generated adjective.
            If False, any generated adjective will be discarded.
        exclude : optional
            List of names we should avoid generating.

        Returns
        -------
        name :
            The whole name, i.e. `adj + " " + noun`.
        adj :
            The adjective part of the name.
        noun :
            The noun part of the name.
        """

        # Get room-specialized name, if possible.
        symbol = "#{}_({})#".format(room_type, obj_type)
        if not self.has_tag(symbol):
            # Otherwise, fallback on the generic object names.
            symbol = "#({})#".format(obj_type)

        # We don't want to generate a name that is in `exclude`.
        found_candidate = False
        for i in range(50):  # We default to fifty attempts
            candidate = self.expand(symbol)
            name, adj, noun = self.split_name_adj_noun(candidate, include_adj)

            if name not in exclude:
                found_candidate = True
                break

        if not found_candidate:
            # Not enough variation for the object we want to name.
            # Warn the user and fall back on adding an adjective if we can.
            if not include_adj:
                name, adj, noun = self.generate_name(obj_type, room_type, include_adj=True, exclude=exclude)
                msg = ("Not enough variation for '{}'. Falling back on using adjective '{}'."
                       " To avoid this message you can add more variation in the '{}'"
                       " related grammar files located in '{}'.")
                msg = msg.format(symbol, adj, self.theme, data.get_text_grammars_path())
                warnings.warn(msg, textworld.TextworldGenerationWarning)
                return name, adj, noun

            # Still not enough variation for the object we want to name.
            if not self.allowed_variables_numbering:
                msg = ("Not enough variation for '{}'. You can add more variation"
                       " in the '{}' related grammar files located in '{}'"
                       " or turn on the 'include_adj=True' grammar flag."
                       " In last resort, you could always turn on the"
                       " 'allowed_variables_numbering=True' grammar flag"
                       " to append unique number to object name.")
                msg = msg.format(symbol, self.theme, data.get_text_grammars_path())
                raise ValueError(msg)

            if obj_type not in self.overflow_dict:
                self.overflow_dict[obj_type] = []

            # Append unique (per type) number to the noun.
            suffix = " {}".format(len(self.overflow_dict[obj_type]))
            noun += suffix
            name += suffix
            self.overflow_dict[obj_type].append(name)

        return name, adj, noun

    def get_vocabulary(self) -> List[str]:
        seen = set()
        all_words = set()
        pattern = re.compile(r'[#][^#]*[#]')
        to_expand = list(self.grammar.keys())
        while len(to_expand) > 0:
            tag = to_expand.pop()
            if tag in seen:
                continue

            seen.add(tag)

            words = tag.split()
            for word in words:
                if pattern.match(word):
                    for to_replace in pattern.findall(word):
                        for replacement in self.grammar[to_replace]:
                            to_expand.append(word.replace(to_replace, replacement))

                else:
                    all_words.add(word)

        return sorted(all_words)

    def get_all_expansions_for_tag(self, tag: str, max_depth: int = 500) -> List[str]:
        """
        Get all possible expansions for a grammar tag.

        Parameters
        ----------
        tag :
            Grammar tag to be expanded.
        max_depth : optional
            Maximum recursion depth when expanding tag.

        Returns
        -------
        expansions :
            All possible expansions.
        """
        if tag not in self.grammar:
            return []

        variants = []

        # Recursively get all symbol possibilities
        def _iterate(tag, depth):
            if "#" in tag and depth < max_depth:
                depth += 1
                to_replace = re.findall(r'[#][^#]*[#]', tag)
                for replace in to_replace:
                    for rhs in self.grammar[replace]:
                        _iterate(tag.replace(replace, rhs), depth)
            else:
                variants.append(tag)

        _iterate(tag, 0)
        return variants

    def get_all_expansions_for_type(self, type: str):
        """
        Get all possible expansions for a given object type.

        Parameters
        ----------
        type :
            Object type.

        Returns
        -------
        names :
            All possible names.
        """
        expansions = self.get_all_expansions_for_tag("#({})#".format(type))
        for room_type in self.grammar["#room_type#"]:
            expansions += self.get_all_expansions_for_tag("#{}_({})#".format(room_type, type))

        return uniquify(expansions)

    def get_all_names_for_type(self, type: str, include_adj: True):
        """
        Get all possible names for a given object type.

        Parameters
        ----------
        type :
            Object type.
        include_adj : optional
            If True, names can contain generated adjectives.
            If False, any generated adjectives will be discarded.

        Returns
        -------
        names :
            All possible names sorted in alphabetical order.
        """
        expansions = self.get_all_expansions_for_type(type)
        names = [self.split_name_adj_noun(expansion, include_adj)[0] for expansion in expansions]
        return sorted(set(names))

    def get_all_adjective_for_type(self, type: str):
        """
        Get all possible adjectives for a given object type.

        Parameters
        ----------
        type :
            Object type.

        Returns
        -------
        adjectives :
            All possible adjectives sorted in alphabetical order.
        """
        expansions = self.get_all_expansions_for_type(type)
        adjectives = [self.split_name_adj_noun(expansion, include_adj=True)[1] for expansion in expansions]
        return sorted(set(adjectives))

    def get_all_nouns_for_type(self, type: str):
        """
        Get all possible nouns for a given object type.

        Parameters
        ----------
        type :
            Object type.

        Returns
        -------
        nouns :
            All possible nouns sorted in alphabetical order.
        """
        expansions = self.get_all_expansions_for_type(type)
        nouns = [self.split_name_adj_noun(expansion, include_adj=False)[2] for expansion in expansions]
        return sorted(set(nouns))

    def check(self) -> bool:
        """
        Check if this grammar is valid.

        TODO: use logging mechanism to report warnings and errors.
        """
        errors_found = False
        for symbol in self.grammar:
            if len(self.grammar[symbol]) == 0:
                print("[Warning] Symbol {} has empty tags".format(symbol))

            for tag in self.grammar[symbol]:
                if tag == "":
                    print("[Warning] Symbol {} has empty tags".format(symbol))

                for symb in re.findall(r'[#][^#]*[#]', tag):
                    if symb not in self.grammar:
                        print("[Error] Symbol {} not found in grammar (Occurs in expansion of {})".format(symb, symbol))
                        errors_found = True

        return not errors_found
