# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import glob
import re
import warnings
from os.path import join as pjoin
from collections import OrderedDict, defaultdict
from typing import Any, Optional, Mapping, List, Tuple, Container, Union

from numpy.random import RandomState

import textworld
from textworld import g_rng
from textworld.utils import uniquify
from textworld.generator.data import KnowledgeBase
from textworld.textgen import TextGrammar


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


class MissingTextGrammar(NameError):
    def __init__(self, path):
        msg = "Cannot find any theme files: {path}."
        super().__init__(msg.format(path=path))


class GrammarOptions:
    __slots__ = ['theme', 'names_to_exclude', 'include_adj', 'blend_descriptions',
                 'ambiguous_instructions', 'only_last_action',
                 'blend_instructions',
                 'allowed_variables_numbering', 'unique_expansion']

    def __init__(self, options=None, **kwargs):
        if isinstance(options, GrammarOptions):
            options = options.serialize()

        options = options or kwargs

        #: str: Grammar theme's name. All `*.twg` files starting with that name will be loaded.
        self.theme = options.get("theme", "house")
        #: List[str]: List of names the text generation should not use.
        self.names_to_exclude = list(options.get("names_to_exclude", []))
        #: bool: Append numbers after an object name if there is not enough variation for it.
        self.allowed_variables_numbering = options.get("allowed_variables_numbering", False)
        #: bool: When True, #symbol# are force to be expanded to unique text.
        self.unique_expansion = options.get("unique_expansion", False)
        #: bool: When True, object names can be preceeded by an adjective.
        self.include_adj = options.get("include_adj", False)
        #: bool: When True, only the last action of a quest will be described
        #:       in the generated objective.
        self.only_last_action = options.get("only_last_action", False)
        #: bool: When True, consecutive actions to be accomplished might be
        #:       described in a single sentence rather than separate ones.
        self.blend_instructions = options.get("blend_instructions", False)
        #: bool: When True, objects sharing some properties might be described
        #:       in a single sentence rather than separate consecutive ones.
        self.blend_descriptions = options.get("blend_descriptions", False)
        #: bool: When True, in the game objective, objects of interest might
        #:       be refer to by their type or adjective rather than full name.
        self.ambiguous_instructions = options.get("ambiguous_instructions", False)

    def serialize(self) -> Mapping:
        """ Serialize this object.

        Results:
            GrammarOptions's data serialized to be JSON compatible.
        """
        return {slot: getattr(self, slot) for slot in self.__slots__}

    @classmethod
    def deserialize(cls, data: Mapping) -> "GrammarOptions":
        """ Creates a `GrammarOptions` from serialized data.

        Args:
            data: Serialized data with the needed information to build a
                  `GrammarOptions` object.
        """
        return cls(data)

    def copy(self) -> "GrammarOptions":
        return GrammarOptions.deserialize(self.serialize())

    def __eq__(self, other) -> bool:
        return (isinstance(other, GrammarOptions)
                and all(getattr(self, slot) == getattr(other, slot) for slot in self.__slots__))

    @property
    def uuid(self) -> str:
        """ Generate UUID for this set of grammar options. """
        def _unsigned(n):
            return n & 0xFFFFFFFFFFFFFFFF

        # Skip theme and names_to_exclude.
        values = [int(getattr(self, s)) for s in self.__slots__[2:]]
        option = "".join(map(str, values))

        from hashids import Hashids
        hashids = Hashids(salt="TextWorld")
        if len(self.names_to_exclude) > 0:
            names_to_exclude_hash = _unsigned(hash(frozenset(self.names_to_exclude)))
            return self.theme + "-" + hashids.encode(names_to_exclude_hash) + "-" + hashids.encode(int(option))

        return self.theme + "-" + hashids.encode(int(option))

    def __str__(self) -> str:
        infos = []
        for slot in self.__slots__:
            infos.append("{}: {}".format(slot, getattr(self, slot)))

        return "\n".join(infos)


class Grammar:
    """
    Context-Free Grammar for text generation.
    """

    _cache = {}

    def __init__(self, options: Union[GrammarOptions, Mapping[str, Any]] = {}, rng: Optional[RandomState] = None):
        """
        Arguments:
            options:
                For customizing text generation process (see
                :py:class:`textworld.generator.GrammarOptions <textworld.generator.text_grammar.GrammarOptions>`
                for the list of available options).
            rng:
                Random generator used for sampling tag expansions.
        """
        self.options = GrammarOptions(options)
        self.grammar = OrderedDict()
        self.rng = g_rng.next() if rng is None else rng
        self.allowed_variables_numbering = self.options.allowed_variables_numbering
        self.unique_expansion = self.options.unique_expansion
        self.all_expansions = defaultdict(list)

        # The current used symbols
        self.overflow_dict = OrderedDict()
        self.used_names = set(self.options.names_to_exclude)

        # Load the grammar associated to the provided theme.
        self.theme = self.options.theme

        # Load the object names file
        path = pjoin(KnowledgeBase.default().text_grammars_path, glob.escape(self.theme) + "*.twg")
        files = glob.glob(path)
        if len(files) == 0:
            raise MissingTextGrammar(path)

        for filename in files:
            self._parse(filename)

    def __eq__(self, other):
        return (isinstance(other, Grammar)
                and self.overflow_dict == other.overflow_dict
                and self.grammar == other.grammar
                and self.options.uuid == other.options.uuid
                and self.used_names == other.used_names)

    def _parse(self, path: str):
        """
        Parse lines and add them to the grammar.
        """
        if path not in self._cache:
            with open(path) as f:
                self._cache[path] = TextGrammar.parse(f.read(), filename=path)

        for name, rule in self._cache[path].rules.items():
            self.grammar["#" + name + "#"] = rule

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
            expansion = rng.choice(self.grammar[tag].alternatives)
            expansion = expansion.full_form()
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
                      include_adj: Optional[bool] = None, exclude: Container[str] = []) -> Tuple[str, str, str]:
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
            Default: use value grammar.options.include_adj
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
        if include_adj is None:
            include_adj = self.options.include_adj

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
                msg = msg.format(symbol, adj, self.theme, KnowledgeBase.default().text_grammars_path)
                warnings.warn(msg, textworld.GenerationWarning)
                return name, adj, noun

            # Still not enough variation for the object we want to name.
            if not self.allowed_variables_numbering:
                msg = ("Not enough variation for '{}'. You can add more variation"
                       " in the '{}' related grammar files located in '{}'"
                       " or turn on the 'include_adj=True' grammar flag."
                       " In last resort, you could always turn on the"
                       " 'allowed_variables_numbering=True' grammar flag"
                       " to append unique number to object name.")
                msg = msg.format(symbol, self.theme, KnowledgeBase.default().text_grammars_path)
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
        i7_pattern = re.compile(r'\[[^]]*\]')
        tw_pattern = re.compile(r'\((obj|name[^)]*|action|list_of_actions)\)')
        to_expand = list(self.grammar.keys())
        while len(to_expand) > 0:
            tag = to_expand.pop()
            if tag in seen:
                continue

            seen.add(tag)

            # Remove i7 code snippets.
            tag = i7_pattern.sub(" ", tag)
            # Remove all TW placeholders.
            tag = tw_pattern.sub(" ", tag)

            words = tag.split()
            for word in words:
                if pattern.search(word):
                    for to_replace in pattern.findall(word):
                        for alternative in self.grammar[to_replace].alternatives:
                            to_expand.append(word.replace(to_replace, alternative.full_form()))

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
                    for rhs in self.grammar[replace].alternatives:
                        _iterate(tag.replace(replace, rhs.full_form()), depth)
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
        for room_type in self.grammar["#room_type#"].alternatives:
            expansions += self.get_all_expansions_for_tag("#{}_({})#".format(room_type.full_form(), type))

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
            if len(self.grammar[symbol].alternatives) == 0:
                print("[Warning] Symbol {} has empty tags".format(symbol))

            for tag in self.grammar[symbol].alternatives:
                tag = tag.full_form()
                if tag == "":
                    print("[Warning] Symbol {} has empty tags".format(symbol))

                for symb in re.findall(r'[#][^#]*[#]', tag):
                    if symb not in self.grammar:
                        print("[Error] Symbol {} not found in grammar (Occurs in expansion of {})".format(symb, symbol))
                        errors_found = True

        return not errors_found
