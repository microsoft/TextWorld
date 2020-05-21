# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from collections import Counter, defaultdict, deque
from functools import total_ordering, lru_cache
from tatsu.model import NodeWalker
import textwrap
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Set, Sequence

try:
    from typing import Collection
except ImportError:
    # Collection is new in Python 3.6 -- fall back on Iterable for 3.5
    from typing import Iterable as Collection

from textworld.logic.model import GameLogicModelBuilderSemantics
from textworld.logic.parser import GameLogicParser
from textworld.utils import uniquify, unique_product

from mementos import memento_factory, with_metaclass


# We use first-order logic to represent the state of the world, and the actions
# that can be applied to it.  The relevant classes are:
#
# - Variable: a logical variable representing an entity in the world
#
# - Proposition: a predicate applied to some variables, e.g. in(cup, kitchen)
#
# - Action: an action that modifies the state of the world, with propositions as
#   pre-/post-conditions
#
# - State: holds the set of factual propositions in the current world state
#
# - Placeholder: a formal parameter to a predicate
#
# - Predicate: an unevaluated predicate, e.g. in(object, container)
#
# - Rule: a template for an action, with predicates as pre-/post-conditions

# Performance note: many of these classes are performance-critical.  The
# optimization techniques used in their implementation include:
#
# - Immutability, which enables heavy object sharing
#
# - Using __slots__ to save memory and speed up attribute access
#
# - For classes that appear as dictionary keys or in sets, we cache the hash
#   code in the _hash field
#
# - For those same classes, we implement __eq__() like this:
#       return self.attr1 == other.attr1 and self.attr2 == other.attr2
#   rather than like this:
#       return (self.attr1, self.attr2) == (other.attr1, other.attr2)
#   to avoid allocating tuples
#
# - List comprehensions are preferred to generator expressions


def _check_type_conflict(name, old_type, new_type):
    if old_type != new_type:
        raise ValueError("Conflicting types for `{}`: have `{}` and `{}`.".format(name, old_type, new_type))


class _ModelConverter(NodeWalker):
    """
    Converts TatSu model objects to our types.
    """

    def __init__(self, logic=None):
        super().__init__()
        self._cache = {}
        self._logic = logic

    def _unescape(self, string):
        # Strip quotation marks
        return string[1:-1]

    def _unescape_block(self, string):
        # Strip triple quotation marks and dedent
        string = string[3:-3]
        return textwrap.dedent(string)

    def walk_list(self, l):
        return [self.walk(node) for node in l]

    def _walk_variable_ish(self, node, cls):
        name = node.name
        result = cls(name, node.type)

        cached = self._cache.get(name)
        if cached:
            _check_type_conflict(name, cached.type, result.type)
            result = cached
        else:
            self._cache[name] = result

        return result

    def _walk_action_ish(self, node, cls):
        self._cache.clear()

        pre = []
        post = []

        for precondition in node.preconditions:
            condition = self.walk(precondition.condition)
            pre.append(condition)
            if precondition.preserve:
                post.append(condition)

        post.extend(self.walk(node.postconditions))

        return cls(node.name, pre, post)

    def walk_VariableNode(self, node):
        return self._walk_variable_ish(node, Variable)

    def walk_SignatureNode(self, node):
        return Signature(node.name, node.types)

    def walk_PropositionNode(self, node):
        return Proposition(node.name, self.walk(node.arguments))

    def walk_ActionNode(self, node):
        return self._walk_action_ish(node, Action)

    def walk_PlaceholderNode(self, node):
        return self._walk_variable_ish(node, Placeholder)

    def walk_PredicateNode(self, node):
        return Predicate(node.name, self.walk(node.parameters))

    def walk_RuleNode(self, node):
        return self._walk_action_ish(node, Rule)

    def walk_AliasNode(self, node):
        return Alias(self.walk(node.lhs), self.walk(node.rhs))

    def walk_PredicatesNode(self, node):
        for pred_or_alias in self.walk(node.predicates):
            if isinstance(pred_or_alias, Signature):
                self._logic._add_predicate(pred_or_alias)
            else:
                self._logic._add_alias(pred_or_alias)

    def walk_RulesNode(self, node):
        for rule in self.walk(node.rules):
            self._logic._add_rule(rule)

    def walk_ReverseRuleNode(self, node):
        self._logic._add_reverse_rule(node.lhs, node.rhs)

    def walk_ReverseRulesNode(self, node):
        self.walk(node.reverse_rules)

    def walk_ConstraintsNode(self, node):
        for constraint in self.walk(node.constraints):
            self._logic._add_constraint(constraint)

    def walk_Inform7TypeNode(self, node):
        name = self._type.name
        kind = self._unescape(node.kind)
        definition = self._unescape(node.definition) if node.definition else None
        self._logic.inform7._add_type(Inform7Type(name, kind, definition))

    def walk_Inform7PredicateNode(self, node):
        return Inform7Predicate(self.walk(node.predicate), self._unescape(node.source))

    def walk_Inform7PredicatesNode(self, node):
        for i7pred in self.walk(node.predicates):
            self._logic.inform7._add_predicate(i7pred)

    def walk_Inform7CommandNode(self, node):
        return Inform7Command(node.rule, self._unescape(node.command), self._unescape(node.event))

    def walk_Inform7CommandsNode(self, node):
        for i7cmd in self.walk(node.commands):
            self._logic.inform7._add_command(i7cmd)

    def walk_Inform7CodeNode(self, node):
        code = self._unescape_block(node.code)
        self._logic.inform7._add_code(code)

    def walk_Inform7Node(self, node):
        self.walk(node.parts)

    def walk_TypeNode(self, node):
        name = node.name
        supertypes = node.supertypes
        if supertypes is None:
            supertypes = []

        self._type = Type(name, supertypes)
        self._logic.types.add(self._type)

        self.walk(node.parts)

    def walk_DocumentNode(self, node):
        self.walk(node.types)


_PARSER = GameLogicParser(semantics=GameLogicModelBuilderSemantics(), parseinfo=True)


def _parse_and_convert(*args, **kwargs):
    model = _PARSER.parse(*args, **kwargs)
    return _ModelConverter().walk(model)


@total_ordering
class Type:
    """
    A variable type.
    """

    def __init__(self, name: str, parents: Iterable[str]):
        self.name = name
        self.parents = tuple(parents)

    def _attach(self, hier: "TypeHierarchy"):
        self._hier = hier

    @property
    def parent_types(self) -> Iterable["Type"]:
        """
        The parents of this type as Type objects.
        """
        return (self._hier.get(name) for name in self.parents)

    @property
    def ancestors(self) -> Iterable["Type"]:
        """
        The ancestors of this type (not including itself).
        """
        return self._hier.closure(self, lambda t: t.parent_types)

    @property
    def supertypes(self) -> Iterable["Type"]:
        """
        This type and its ancestors.
        """
        yield self
        yield from self.ancestors

    def is_supertype_of(self, other: "Type") -> bool:
        return self in other.supertypes

    def has_supertype_named(self, name: str) -> bool:
        return self._hier.get(name).is_supertype_of(self)

    @property
    def children(self) -> Iterable[str]:
        """
        The names of the direct children of this type.
        """
        return self._hier._children[self.name]

    @property
    def child_types(self) -> Iterable["Type"]:
        """
        The direct children of this type.
        """
        return (self._hier.get(name) for name in self.children)

    @property
    def descendants(self) -> Iterable["Type"]:
        """
        The descendants of this type (not including itself).
        """
        return self._hier.closure(self, lambda t: t.child_types)

    @property
    def subtypes(self) -> Iterable["Type"]:
        """
        This type and its descendants.
        """
        yield self
        yield from self.descendants

    def is_subtype_of(self, other: "Type") -> bool:
        return self in other.subtypes

    def has_subtype_named(self, name: str) -> bool:
        return self._hier.get(name).is_subtype_of(self)

    def __str__(self):
        if self.parents:
            return "{} : {}".format(self.name, ", ".join(self.parents))
        else:
            return self.name

    def __repr__(self):
        return "Type({!r}, {!r})".format(self.name, self.parents)

    def __eq__(self, other):
        if isinstance(other, Type):
            return self.name == other.name
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if isinstance(other, Type):
            return self.name < other.name
        else:
            return NotImplemented


class TypeHierarchy:
    """
    A hierarchy of types.
    """

    def __init__(self):
        self._types = {}
        self._children = defaultdict(list)
        self._cache = {}

    def add(self, type: Type):
        if type.name in self._types:
            raise ValueError("Duplicate type {}".format(type.name))

        type._attach(self)
        self._types[type.name] = type

        for parent in type.parents:
            children = self._children[parent]
            children.append(type.name)
            children.sort()

        # Adding a new type invalidates the cache.
        self._cache = {}

    def get(self, name: str) -> Type:
        return self._types[name]

    def __iter__(self):
        yield from self._types.values()

    def __len__(self):
        return len(self._types)

    def closure(self, type: Type, expand: Callable[[Type], Iterable[Type]]) -> Iterable[Type]:
        r"""
        Compute the transitive closure in a type lattice according to some type
        relationship (generally direct sub-/super-types).

        Such a lattice may look something like this::

              A
             / \
            B   C
             \ /
              D

        so the closure of D would be something like [B, C, A].
        """

        return self._bfs_unique(type, expand)

    def _multi_expand(self, types: Collection[Type], expand: Callable[[Type], Iterable[Type]]) -> Iterable[Collection[Type]]:
        """
        Apply the expand() function to every element of a type sequence in turn.
        """

        for i in range(len(types)):
            expansion = list(types)
            for replacement in expand(expansion[i]):
                expansion[i] = replacement
                yield tuple(expansion)

    def multi_closure(self, types: Collection[Type], expand: Callable[[Type], Iterable[Type]]) -> Iterable[Collection[Type]]:
        r"""
        Compute the transitive closure of a sequence of types in a type lattice
        induced by some per-type relationship (generally direct sub-/super-types).

        For a single type, such a lattice may look something like this::

              A
             / \
            B   C
             \ /
              D

        so the closure of D would be something like [B, C, A].  For multiple
        types at once, the lattice is more complicated::

                        __ (A,A) __
                       /   |   |   \
                  (A,B) (A,C) (B,A) (C,A)
              *******************************
            (A,D) (B,B) (B,C) (C,B) (C,C) (D,A)
              *******************************
                  (B,D) (C,D) (D,B) (D,C)
                       \   |   |   /
                        \_ (D,D) _/
        """

        return self._bfs_unique(types, lambda ts: self._multi_expand(ts, expand))

    def _bfs_unique(self, start, expand):
        """
        Apply breadth-first search, returning only previously unseen nodes.
        """

        seen = set()
        queue = deque(expand(start))
        while queue:
            item = queue.popleft()
            yield item
            for expansion in expand(item):
                if expansion not in seen:
                    seen.add(expansion)
                    queue.append(expansion)

    def multi_ancestors(self, types: Collection[Type]) -> Iterable[Collection[Type]]:
        """
        Compute the ancestral closure of a sequence of types.  If these are the
        types of some variables, the result will be all the function parameter
        types that could also accept those variables.
        """
        return self.multi_closure(types, lambda t: t.parent_types)

    def multi_supertypes(self, types: Collection[Type]) -> Iterable[Collection[Type]]:
        """
        Computes the ancestral closure of a sequence of types, including the
        initial types.
        """
        yield tuple(types)
        yield from self.multi_ancestors(types)

    def multi_descendants(self, types: Collection[Type]) -> Iterable[Collection[Type]]:
        """
        Compute the descendant closure of a sequence of types.  If these are the
        types of some function parameters, the result will be all the variable
        types that could also be passed to this function.
        """
        return self.multi_closure(types, lambda t: t.child_types)

    def multi_subtypes(self, types: Collection[Type]) -> List[Collection[Type]]:
        """
        Computes the descendant closure of a sequence of types, including the
        initial types.
        """
        types = tuple(types)
        if types not in self._cache:
            self._cache[types] = [types] + list(self.multi_descendants(types))

        return self._cache[types]


@total_ordering
class Variable:
    """
    A variable representing an object in a world.
    """

    __slots__ = ("name", "type", "_hash")

    def __init__(self, name: str, type: Optional[str] = None):
        """
        Create a Variable.

        Parameters
        ----------
        name :
            The (unique) name of the variable.
        type : optional
            The type of the variable.  Defaults to the same as the name.
        """

        self.name = name

        if type is None:
            type = name
        self.type = type

        self._hash = hash((self.name, self.type))

    def is_a(self, type: Type) -> bool:
        return type.has_subtype_named(self.type)

    def __str__(self):
        if self.type == self.name:
            return self.name
        else:
            return "{}: {}".format(self.name, self.type)

    def __repr__(self):
        return "Variable({!r}, {!r})".format(self.name, self.type)

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name and self.type == other.type
        else:
            return NotImplemented

    def __hash__(self):
        return self._hash

    def __lt__(self, other):
        if isinstance(other, Variable):
            return (self.name, self.type) < (other.name, other.type)
        else:
            return NotImplemented

    @classmethod
    def parse(cls, expr: str) -> "Variable":
        """
        Parse a variable expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name` or `name: type`.
        """
        return _parse_and_convert(expr, rule_name="onlyVariable")

    def serialize(self) -> Mapping:
        return {
            "name": self.name,
            "type": self.type,
        }

    @classmethod
    def deserialize(cls, data: Mapping) -> "Variable":
        return cls(data["name"], data["type"])


SignatureTracker = memento_factory(
    'SignatureTracker',
    lambda cls, args, kwargs: (
        cls,
        kwargs.get("name", args[0] if len(args) >= 1 else None),
        tuple(kwargs.get("types", args[1] if len(args) == 2 else []))
    )
)


@total_ordering
class Signature(with_metaclass(SignatureTracker, object)):
    """
    The type signature of a Predicate or Proposition.
    """

    __slots__ = ("name", "types", "_hash")

    def __init__(self, name: str, types: Iterable[str]):
        """
        Create a Signature.

        Parameters
        ----------
        name :
            The name of the proposition/predicate this signature is for.
        types :
            The types of the parameters to the proposition/predicate.
        """

        self.name = name
        self.types = tuple(types)
        self._hash = hash((self.name, self.types))

    def __str__(self):
        return "{}({})".format(self.name, ", ".join(map(str, self.types)))

    def __repr__(self):
        return "Signature({!r}, {!r})".format(self.name, self.types)

    def __eq__(self, other):
        if isinstance(other, Signature):
            return self.name == other.name and self.types == other.types
        else:
            return NotImplemented

    def __hash__(self):
        return self._hash

    def __lt__(self, other):
        if isinstance(other, Signature):
            return (self.name, self.types) < (other.name, other.types)
        else:
            return NotImplemented

    @classmethod
    def parse(cls, expr: str) -> "Signature":
        """
        Parse a signature expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name(type [, type]*)`.
        """
        return _parse_and_convert(expr, rule_name="onlySignature")


PropositionTracker = memento_factory(
    'PropositionTracker',
    lambda cls, args, kwargs: (
        cls,
        kwargs.get("name", args[0] if len(args) >= 1 else None),
        tuple(v.name for v in kwargs.get("arguments", args[1] if len(args) == 2 else []))
    )
)


@total_ordering
class Proposition(with_metaclass(PropositionTracker, object)):
    """
    An instantiated Predicate, with concrete variables for each placeholder.
    """

    __slots__ = ("name", "arguments", "signature", "_hash")

    def __init__(self, name: str, arguments: Iterable[Variable] = []):
        """
        Create a Proposition.

        Parameters
        ----------
        name :
            The name of the proposition.
        arguments :
            The variables this proposition is applied to.
        """

        self.name = name
        self.arguments = tuple(arguments)
        self.signature = Signature(name, [var.type for var in self.arguments])
        self._hash = hash((self.name, self.arguments))

    @property
    def names(self) -> Collection[str]:
        """
        The names of the variables in this proposition.
        """
        return tuple([var.name for var in self.arguments])

    @property
    def types(self) -> Collection[str]:
        """
        The types of the variables in this proposition.
        """
        return self.signature.types

    def __str__(self):
        return "{}({})".format(self.name, ", ".join(map(str, self.arguments)))

    def __repr__(self):
        return "Proposition({!r}, {!r})".format(self.name, self.arguments)

    def __eq__(self, other):
        if isinstance(other, Proposition):
            return self.name == other.name and self.arguments == other.arguments
        else:
            return NotImplemented

    def __hash__(self):
        return self._hash

    def __lt__(self, other):
        if isinstance(other, Proposition):
            return (self.name, self.arguments) < (other.name, other.arguments)
        else:
            return NotImplemented

    @classmethod
    def parse(cls, expr: str) -> "Proposition":
        """
        Parse a proposition expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name(variable [, variable]*)`.
        """
        return _parse_and_convert(expr, rule_name="onlyProposition")

    def serialize(self) -> Mapping:
        return {
            "name": self.name,
            "arguments": [var.serialize() for var in self.arguments],
        }

    @classmethod
    def deserialize(cls, data: Mapping) -> "Proposition":
        name = data["name"]
        args = [Variable.deserialize(arg) for arg in data["arguments"]]
        return cls(name, args)


@total_ordering
class Placeholder:
    """
    A symbolic placeholder for a variable in a Predicate.
    """

    __slots__ = ("name", "type", "_hash")

    def __init__(self, name: str, type: Optional[str] = None):
        """
        Create a Placeholder.

        Parameters
        ----------
        name :
            The name of this placeholder.
        type : optional
            The type of variable represented.  Defaults to the name with any trailing apostrophes stripped.
        """

        self.name = name

        if type is None:
            type = name.rstrip("'")
        self.type = type

        self._hash = hash((self.name, self.type))

    def __str__(self):
        if self.type == self.name.rstrip("'"):
            return self.name
        else:
            return "{}: {}".format(self.name, self.type)

    def __repr__(self):
        return "Placeholder({!r}, {!r})".format(self.name, self.type)

    def __eq__(self, other):
        if isinstance(other, Placeholder):
            return self.name == other.name and self.type == other.type
        else:
            return NotImplemented

    def __hash__(self):
        return self._hash

    def __lt__(self, other):
        if isinstance(other, Placeholder):
            return (self.name, self.type) < (other.name, other.type)
        else:
            return NotImplemented

    @classmethod
    def parse(cls, expr: str) -> "Placeholder":
        """
        Parse a placeholder expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name` or `name: type`.
        """
        return _parse_and_convert(expr, rule_name="onlyPlaceholder")

    def serialize(self) -> Mapping:
        return {
            "name": self.name,
            "type": self.type,
        }

    @classmethod
    def deserialize(cls, data: Mapping) -> "Placeholder":
        return cls(data["name"], data["type"])


@total_ordering
class Predicate:
    """
    A boolean-valued function over variables.
    """

    def __init__(self, name: str, parameters: Iterable[Placeholder]):
        """
        Create a Predicate.

        Parameters
        ----------
        name :
            The name of this predicate.
        parameters :
            The symbolic arguments to this predicate.
        """

        self.name = name
        self.parameters = tuple(parameters)
        self.signature = Signature(name, [ph.type for ph in self.parameters])

    @property
    def names(self) -> Collection[str]:
        """
        The names of the placeholders in this predicate.
        """
        return tuple([ph.name for ph in self.parameters])

    @property
    def types(self) -> Collection[str]:
        """
        The types of the placeholders in this predicate.
        """
        return self.signature.types

    def __str__(self):
        return "{}({})".format(self.name, ", ".join(map(str, self.parameters)))

    def __repr__(self):
        return "Predicate({!r}, {!r})".format(self.name, self.parameters)

    def __eq__(self, other):
        if isinstance(other, Predicate):
            return (self.name, self.parameters) == (other.name, other.parameters)
        else:
            return NotImplemented

    def __hash__(self):
        return hash((self.name, self.parameters))

    def __lt__(self, other):
        if isinstance(other, Predicate):
            return (self.name, self.parameters) < (other.name, other.parameters)
        else:
            return NotImplemented

    @classmethod
    def parse(cls, expr: str) -> "Predicate":
        """
        Parse a predicate expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name(placeholder [, placeholder]*)`.
        """
        return _parse_and_convert(expr, rule_name="onlyPredicate")

    def serialize(self) -> Mapping:
        return {
            "name": self.name,
            "parameters": [ph.serialize() for ph in self.parameters],
        }

    @classmethod
    def deserialize(cls, data: Mapping) -> "Predicate":
        name = data["name"]
        params = [Placeholder.deserialize(ph) for ph in data["parameters"]]
        return cls(name, params)

    def substitute(self, mapping: Mapping[Placeholder, Placeholder]) -> "Predicate":
        """
        Copy this predicate, substituting certain placeholders for others.

        Parameters
        ----------
        mapping :
            A mapping from old to new placeholders.
        """

        params = [mapping.get(param, param) for param in self.parameters]
        return Predicate(self.name, params)

    def instantiate(self, mapping: Mapping[Placeholder, Variable]) -> Proposition:
        """
        Instantiate this predicate with the given mapping.

        Parameters
        ----------
        mapping :
            A mapping from Placeholders to Variables.

        Returns
        -------
        The instantiated Proposition with each Placeholder mapped to the corresponding Variable.
        """

        args = [mapping[param] for param in self.parameters]
        return Proposition(self.name, args)

    def match(self, proposition: Proposition) -> Optional[Mapping[Placeholder, Variable]]:
        """
        Match this predicate against a concrete proposition.

        Parameters
        ----------
        proposition :
            The proposition to match against.

        Returns
        -------
        The mapping from placeholders to variables such that `self.instantiate(mapping) == proposition`, or `None` if no
        such mapping exists.
        """

        if self.name != proposition.name:
            return None
        else:
            return {ph: var for ph, var in zip(self.parameters, proposition.arguments)}


class Alias:
    """
    A shorthand predicate alias.
    """

    def __init__(self, pattern: Predicate, replacement: Iterable[Predicate]):
        self.pattern = pattern
        self.replacement = tuple(replacement)

    def __str__(self):
        return "{} = {}".format(self.pattern, " & ".join(map(str, self.replacement)))

    def __repr__(self):
        return "Alias({!r}, {!r})".format(self.pattern, self.replacement)

    def expand(self, predicate: Predicate) -> Collection[Predicate]:
        """
        Expand a use of this alias into its replacement.
        """
        if predicate.signature == self.pattern.signature:
            mapping = dict(zip(self.pattern.parameters, predicate.parameters))
            return tuple([pred.substitute(mapping) for pred in self.replacement])
        else:
            return predicate


class Action:
    """
    An action in the environment.
    """

    def __init__(self, name: str, preconditions: Iterable[Proposition], postconditions: Iterable[Proposition]):
        """
        Create an Action.

        Parameters
        ----------
        name :
            The name of this action.
        preconditions :
            The preconditions that must hold before this action is applied.
        postconditions :
            The conditions that replace the preconditions once applied.
        """

        self.name = name
        self.command_template = None
        self.reverse_name = None
        self.reverse_command_template = None
        self.preconditions = tuple(preconditions)
        self.postconditions = tuple(postconditions)

        self._pre_set = frozenset(self.preconditions)
        self._post_set = frozenset(self.postconditions)

    @property
    def variables(self):
        if not hasattr(self, "_variables"):
            self._variables = tuple(uniquify(var for prop in self.all_propositions for var in prop.arguments))

        return self._variables

    @property
    def all_propositions(self) -> Collection[Proposition]:
        """
        All the pre- and post-conditions.
        """
        return self.preconditions + self.postconditions

    @property
    def added(self) -> Collection[Proposition]:
        """
        All the new propositions being introduced by this action.
        """
        return self._post_set - self._pre_set

    @property
    def removed(self) -> Collection[Proposition]:
        """
        All the old propositions being removed by this action.
        """
        return self._pre_set - self._post_set

    def __str__(self):
        # Infer carry-over preconditions for pretty-printing
        pre = []
        for prop in self.preconditions:
            if prop in self._post_set:
                pre.append("$" + str(prop))
            else:
                pre.append(str(prop))

        post = [str(prop) for prop in self.postconditions if prop not in self._pre_set]

        return "{} :: {} -> {}".format(self.name, " & ".join(pre), " & ".join(post))

    def __repr__(self):
        return "Action({!r}, {!r}, {!r})".format(self.name, self.preconditions, self.postconditions)

    def __eq__(self, other):
        if isinstance(other, Action):
            return (self.name, self._pre_set, self._post_set) == (other.name, other._pre_set, other._post_set)
        else:
            return NotImplemented

    def __hash__(self):
        return hash((self.name, self._pre_set, self._post_set))

    @classmethod
    def parse(cls, expr: str) -> "Action":
        """
        Parse an action expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name :: [$]proposition [& [$]proposition]* -> proposition [& proposition]*`.
        """
        return _parse_and_convert(expr, rule_name="onlyAction")

    def serialize(self) -> Mapping:
        return {
            "name": self.name,
            "preconditions": [prop.serialize() for prop in self.preconditions],
            "postconditions": [prop.serialize() for prop in self.postconditions],
            "command_template": self.command_template,
            "reverse_name": self.reverse_name,
            "reverse_command_template": self.reverse_command_template,
        }

    @classmethod
    def deserialize(cls, data: Mapping) -> "Action":
        name = data["name"]
        pre = [Proposition.deserialize(prop) for prop in data["preconditions"]]
        post = [Proposition.deserialize(prop) for prop in data["postconditions"]]
        action = cls(name, pre, post)
        action.command_template = data.get("command_template")
        action.reverse_name = data.get("reverse_name")
        action.reverse_command_template = data.get("reverse_command_template")
        return action

    def inverse(self, name: Optional[str] = None) -> "Action":
        """
        Invert the direction of this action.

        Parameters
        ----------
        name : optional
            The new name for the inverse action.

        Returns
        -------
        An action that does the exact opposite of this one.
        """
        name = name or self.reverse_name or "r_" + self.name
        action = Action(name, self.postconditions, self.preconditions)
        action.command_template = self.reverse_command_template
        action.reverse_command_template = self.command_template
        return action

    def format_command(self, mapping: Dict[str, str] = {}):
        mapping = mapping or {v.name: v.name for v in self.variables}
        return self.command_template.format(**mapping)


class Rule:
    """
    A template for an action.
    """

    def __init__(self, name: str, preconditions: Iterable[Predicate], postconditions: Iterable[Predicate]):
        """
        Create a Rule.

        Parameters
        ----------
        name :
            The name of this rule.
        preconditions :
            The preconditions that must hold before this rule is applied.
        postconditions :
            The conditions that replace the preconditions once applied.
        """

        self.name = name
        self.command_template = None
        self.reverse_rule = None
        self._cache = {}
        self.preconditions = tuple(preconditions)
        self.postconditions = tuple(postconditions)

        self._pre_set = frozenset(self.preconditions)
        self._post_set = frozenset(self.postconditions)

        self.placeholders = tuple(uniquify(ph for pred in self.all_predicates for ph in pred.parameters))

    @property
    def all_predicates(self) -> Iterable[Predicate]:
        """
        All the pre- and post-conditions.
        """
        return self.preconditions + self.postconditions

    def __str__(self):
        # Infer carry-over preconditions for pretty-printing
        pre = []
        for pred in self.preconditions:
            if pred in self._post_set:
                pre.append("$" + str(pred))
            else:
                pre.append(str(pred))

        post = [str(pred) for pred in self.postconditions if pred not in self._pre_set]

        return "{} :: {} -> {}".format(self.name, " & ".join(pre), " & ".join(post))

    def __repr__(self):
        return "Rule({!r}, {!r}, {!r})".format(self.name, self.preconditions, self.postconditions)

    def __eq__(self, other):
        if isinstance(other, Rule):
            return (self.name, self._pre_set, self._post_set) == (other.name, other._pre_set, other._post_set)
        else:
            return NotImplemented

    def __hash__(self):
        return hash((self.name, self._pre_set, self._post_set))

    @classmethod
    def parse(cls, expr: str) -> "Rule":
        """
        Parse a rule expression.

        Parameters
        ----------
        expr :
            The string to parse, in the form `name :: [$]predicate [& [$]predicate]* -> predicate [& predicate]*`.
        """
        return _parse_and_convert(expr, rule_name="onlyRule")

    def serialize(self) -> Mapping:
        return {
            "name": self.name,
            "preconditions": [pred.serialize() for pred in self.preconditions],
            "postconditions": [pred.serialize() for pred in self.postconditions],
        }

    @classmethod
    def deserialize(cls, data: Mapping) -> "Rule":
        name = data["name"]
        pre = [Predicate.deserialize(pred) for pred in data["preconditions"]]
        post = [Predicate.deserialize(pred) for pred in data["postconditions"]]
        return cls(name, pre, post)

    def _make_command_template(self, mapping: Mapping[Placeholder, Variable]) -> str:
        if self.command_template is None:
            return None

        substitutions = {ph.name: "{{{}}}".format(var.name) for ph, var in mapping.items()}
        return self.command_template.format(**substitutions)

    def substitute(self, mapping: Mapping[Placeholder, Placeholder], name=None) -> "Rule":
        """
        Copy this rule, substituting certain placeholders for others.

        Parameters
        ----------
        mapping :
            A mapping from old to new placeholders.
        """

        if name is None:
            name = self.name
        pre_subst = [pred.substitute(mapping) for pred in self.preconditions]
        post_subst = [pred.substitute(mapping) for pred in self.postconditions]
        return Rule(name, pre_subst, post_subst)

    def instantiate(self, mapping: Mapping[Placeholder, Variable]) -> Action:
        """
        Instantiate this rule with the given mapping.

        Parameters
        ----------
        mapping :
            A mapping from Placeholders to Variables.

        Returns
        -------
        The instantiated Action with each Placeholder mapped to the corresponding Variable.
        """

        key = tuple(mapping[ph] for ph in self.placeholders)
        if key in self._cache:
            return self._cache[key]

        pre_inst = [pred.instantiate(mapping) for pred in self.preconditions]
        post_inst = [pred.instantiate(mapping) for pred in self.postconditions]
        action = Action(self.name, pre_inst, post_inst)

        action.command_template = self._make_command_template(mapping)
        if self.reverse_rule:
            action.reverse_name = self.reverse_rule.name
            action.reverse_command_template = self.reverse_rule._make_command_template(mapping)

        self._cache[key] = action
        return action

    def match(self, action: Action) -> Optional[Mapping[Placeholder, Variable]]:
        """
        Match this rule against a concrete action.

        Parameters
        ----------
        action :
            The action to match against.

        Returns
        -------
        The mapping from placeholders to variables such that `self.instantiate(mapping) == action`, or `None` if no such
        mapping exists.
        """

        if self.name != action.name:
            return None

        candidates = [action.variables] * len(self.placeholders)

        # A same variable can't be assigned to different placeholders.
        # Using `unique_product` avoids generating those in the first place.
        for assignment in unique_product(*candidates):
            mapping = {ph: var for ph, var in zip(self.placeholders, assignment)}
            if self.instantiate(mapping) == action:
                return mapping

        return None

    def inverse(self, name=None) -> "Rule":
        """
        Invert the direction of this rule.

        Parameters
        ----------
        name : optional
            The new name for the inverse rule.

        Returns
        -------
        A rule that does the exact opposite of this one.
        """

        if name is None:
            name = self.name
            if self.reverse_rule:
                name = self.reverse_rule.name

        if self.reverse_rule:
            return self.reverse_rule

        rule = Rule(name, self.postconditions, self.preconditions)
        rule.reverse_rule = self
        return rule


class Inform7Type:
    """
    Information about an Inform 7 kind.
    """

    def __init__(self, name: str, kind: str, definition: Optional[str] = None):
        self.name = name
        self.kind = kind
        self.definition = definition


class Inform7Predicate:
    """
    Information about an Inform 7 predicate.
    """

    def __init__(self, predicate: Predicate, source: str):
        self.predicate = predicate
        self.source = source

    def __str__(self):
        return '{} :: "{}"'.format(self.predicate, self.source)

    def __repr__(self):
        return "Inform7Predicate({!r}, {!r})".format(self.predicate, self.source)


class Inform7Command:
    """
    Information about an Inform 7 command.
    """

    def __init__(self, rule: str, command: str, event: str):
        self.rule = rule
        self.command = command
        self.event = event

    def __str__(self):
        return '{} :: "{}" :: "{}"'.format(self.rule, self.command, self.event)

    def __repr__(self):
        return "Inform7Command({!r}, {!r}, {!r})".format(self.rule, self.command, self.event)


class Inform7Logic:
    """
    The Inform 7 bindings of a GameLogic.
    """

    def __init__(self):
        self.types = {}
        self.predicates = {}
        self.commands = {}
        self.code = ""

    def _add_type(self, i7type: Inform7Type):
        if i7type.name in self.types:
            raise ValueError("Duplicate Inform 7 type for {}".format(i7type.name))
        self.types[i7type.name] = i7type

    def _add_predicate(self, i7pred: Inform7Predicate):
        sig = i7pred.predicate.signature
        if sig in self.predicates:
            raise ValueError("Duplicate Inform 7 predicate for {}".format(sig))
        self.predicates[sig] = i7pred

    def _add_command(self, i7cmd: Inform7Command):
        rule_name = i7cmd.rule
        if rule_name in self.commands:
            raise ValueError("Duplicate Inform 7 command for {}".format(rule_name))
        self.commands[rule_name] = i7cmd

    def _add_code(self, code: str):
        self.code += code + "\n"

    def _initialize(self, logic):
        self._expand_predicates(logic)
        self._initialize_commands(logic)

    def _expand_predicates(self, logic):
        for sig, pred in list(self.predicates.items()):
            params = pred.predicate.parameters
            types = [logic.types.get(ph.type) for ph in params]
            for descendant in logic.types.multi_descendants(types):
                mapping = {ph: Placeholder(ph.name, type.name) for ph, type in zip(params, descendant)}
                expanded = pred.predicate.substitute(mapping)
                self._add_predicate(Inform7Predicate(expanded, pred.source))

    def _initialize_commands(self, logic):
        for name, command in list(self.commands.items()):
            rule = logic.rules.get(name)
            if not rule:
                continue

            rule.command_template = command.command


class GameLogic:
    """
    The logic for a game (types, rules, etc.).
    """

    def __init__(self):
        self._document = ""
        self.types = TypeHierarchy()
        self.predicates = set()
        self.aliases = {}
        self.rules = {}
        self.reverse_rules = {}
        self.constraints = {}
        self.inform7 = Inform7Logic()

    def _add_predicate(self, signature: Signature):
        if signature in self.predicates:
            raise ValueError("Duplicate predicate {}".format(signature))
        if signature in self.aliases:
            raise ValueError("Predicate {} is also an alias".format(signature))
        self.predicates.add(signature)

    def _add_alias(self, alias: Alias):
        sig = alias.pattern.signature
        if sig in self.aliases:
            raise ValueError("Duplicate alias {}".format(alias))
        if sig in self.predicates:
            raise ValueError("Alias {} is also a predicate".format(alias))
        self.aliases[sig] = alias

    def _add_rule(self, rule: Rule):
        if rule.name in self.rules:
            raise ValueError("Duplicate rule {}".format(rule))
        self.rules[rule.name] = rule

    def _add_reverse_rule(self, rule_name, reverse_name):
        if rule_name in self.reverse_rules:
            raise ValueError("Duplicate reverse rule {}".format(rule_name))
        if reverse_name in self.reverse_rules:
            raise ValueError("Duplicate reverse rule {}".format(reverse_name))
        self.reverse_rules[rule_name] = reverse_name
        self.reverse_rules[reverse_name] = rule_name

    def _add_constraint(self, constraint: Rule):
        if constraint.name in self.constraints:
            raise ValueError("Duplicate constraint {}".format(constraint))
        self.constraints[constraint.name] = constraint

    def _parse(self, document: str, path: Optional[str] = None):
        model = _PARSER.parse(document, filename=path)
        _ModelConverter(self).walk(model)
        self._document += document + "\n"

    def _initialize(self):
        self.aliases = {sig: self._expand_alias(alias) for sig, alias in self.aliases.items()}

        self.rules = {name: self.normalize_rule(rule) for name, rule in self.rules.items()}
        self.constraints = {name: self.normalize_rule(rule) for name, rule in self.constraints.items()}

        for name, rule in self.rules.items():
            r_name = self.reverse_rules.get(name)
            if r_name:
                rule.reverse_rule = self.rules[r_name]

        self.inform7._initialize(self)

    def _expand_alias(self, alias):
        return Alias(alias.pattern, self._expand_alias_recursive(alias.replacement, set()))

    def _expand_alias_recursive(self, predicates, used):
        result = []

        for pred in predicates:
            sig = pred.signature

            if sig in used:
                raise ValueError("Cycle of aliases involving {}".format(sig))

            alias = self.aliases.get(pred.signature)
            if alias:
                expansion = alias.expand(pred)
                used.add(pred.signature)
                result.extend(self._expand_alias_recursive(expansion, used))
                used.remove(pred.signature)
            else:
                result.append(pred)

        return result

    def normalize_rule(self, rule: Rule) -> Rule:
        pre = self._normalize_predicates(rule.preconditions)
        post = self._normalize_predicates(rule.postconditions)
        return Rule(rule.name, pre, post)

    def _normalize_predicates(self, predicates):
        result = []
        for pred in predicates:
            alias = self.aliases.get(pred.signature)
            if alias:
                result.extend(alias.expand(pred))
            else:
                result.append(pred)
        return result

    @classmethod
    @lru_cache(maxsize=128, typed=False)
    def parse(cls, document: str) -> "GameLogic":
        result = cls()
        result._parse(document)
        result._initialize()
        return result

    @classmethod
    def load(cls, paths: Iterable[str]):
        result = cls()
        for path in paths:
            with open(path, "r") as f:
                result._parse(f.read(), path=path)
        result._initialize()
        return result

    @classmethod
    def deserialize(cls, data: str) -> "GameLogic":
        return cls.parse(data)

    def serialize(self) -> str:
        return self._document


class State:
    """
    The current state of a world.
    """

    def __init__(self, logic: GameLogic, facts: Iterable[Proposition] = None):
        """
        Create a State.

        Parameters
        ----------
        logic :
            The logic for this state's game.
        facts : optional
            The facts that will be true in this state.
        """

        if not isinstance(logic, GameLogic):
            raise ValueError("Expected a GameLogic, found {}".format(type(logic)))
        self._logic = logic

        self._facts = defaultdict(set)
        self._vars_by_name = {}
        self._vars_by_type = defaultdict(set)
        self._var_counts = Counter()

        if facts:
            self.add_facts(facts)

    @property
    def facts(self) -> Iterable[Proposition]:
        """
        All the facts in the current state.
        """
        for fact_set in self._facts.values():
            yield from fact_set

    def facts_with_signature(self, sig: Signature) -> Set[Proposition]:
        """
        Returns all the known facts with the given signature.
        """
        return self._facts.get(sig, frozenset())

    def add_fact(self, prop: Proposition):
        """
        Add a fact to the state.
        """

        self._facts[prop.signature].add(prop)

        for var in prop.arguments:
            self._add_variable(var)

    def add_facts(self, props: Iterable[Proposition]):
        """
        Add some facts to the state.
        """

        for prop in props:
            self.add_fact(prop)

    def remove_fact(self, prop: Proposition):
        """
        Remove a fact from the state.
        """

        self._facts[prop.signature].discard(prop)

        for var in prop.arguments:
            self._remove_variable(var)

    def remove_facts(self, props: Iterable[Proposition]):
        """
        Remove some facts from the state.
        """

        for prop in props:
            self.remove_fact(prop)

    def is_fact(self, prop: Proposition) -> bool:
        """
        Returns whether a proposition is true in this state.
        """
        return prop in self._facts[prop.signature]

    def are_facts(self, props: Iterable[Proposition]) -> bool:
        """
        Returns whether the propositions are all true in this state.
        """

        for prop in props:
            if not self.is_fact(prop):
                return False

        return True

    @property
    def variables(self) -> Iterable[Variable]:
        """
        All the variables tracked by the current state.
        """
        return self._vars_by_name.values()

    def has_variable(self, var: Variable) -> bool:
        """
        Returns whether this state is aware of the given variable.
        """
        return self._vars_by_name.get(var.name) == var

    def variable_named(self, name: str) -> Variable:
        """
        Returns the variable with the given name, if known.
        """
        return self._vars_by_name[name]

    def variables_of_type(self, type: str) -> Set[Variable]:
        """
        Returns all the known variables of the given type.
        """
        return self._vars_by_type.get(type, frozenset())

    def _add_variable(self, var: Variable):
        name = var.name
        existing = self._vars_by_name.setdefault(name, var)
        _check_type_conflict(name, existing.type, var.type)

        self._vars_by_type[var.type].add(var)
        self._var_counts[name] += 1

    def _remove_variable(self, var: Variable):
        name = var.name
        self._var_counts[name] -= 1
        if self._var_counts[name] == 0:
            del self._var_counts[name]
            del self._vars_by_name[name]
            self._vars_by_type[var.type].remove(var)

    def is_applicable(self, action: Action) -> bool:
        """
        Check if an action is applicable in this state (i.e. its preconditions are met).
        """
        return self.are_facts(action.preconditions)

    def is_sequence_applicable(self, actions: Iterable[Action]) -> bool:
        """
        Check if a sequence of actions are all applicable in this state.
        """

        # The simplest implementation would copy the state and apply all the actions, but that would waste time both in
        # the copy and the variable tracking etc.

        facts = set(self.facts)
        for action in actions:
            old_len = len(facts)
            facts.difference_update(action.preconditions)
            if len(facts) != old_len - len(action.preconditions):
                return False

            facts.update(action.postconditions)

        return True

    def apply(self, action: Action) -> bool:
        """
        Apply an action to the state.

        Parameters
        ----------
        action :
            The action to apply.

        Returns
        -------
        Whether the action could be applied (i.e. whether the preconditions were met).
        """

        if self.is_applicable(action):
            self.add_facts(action.added)
            self.remove_facts(action.removed)
            return True
        else:
            return False

    def apply_on_copy(self, action: Action) -> Optional["State"]:
        """
        Apply an action to a copy of this state.

        Parameters
        ----------
        action :
            The action to apply.

        Returns
        -------
        The copied state after the action has been applied or `None` if action
        wasn't applicable.
        """
        if not self.is_applicable(action):
            return None

        state = self.copy()
        state.apply(action)
        return state

    def all_applicable_actions(self, rules: Iterable[Rule],
                               mapping: Mapping[Placeholder, Variable] = None) -> Iterable[Action]:
        """
        Get all the rule instantiations that would be valid actions in this state.

        Parameters
        ----------
        rules :
            The possible rules to instantiate.
        mapping : optional
            An initial mapping to start from, constraining the possible instantiations.

        Returns
        -------
        The actions that can be instantiated from the given rules in this state.
        """

        for rule in rules:
            yield from self.all_instantiations(rule, mapping)

    def all_instantiations(self,
                           rule: Rule,
                           mapping: Mapping[Placeholder, Variable] = None
                           ) -> Iterable[Action]:
        """
        Find all possible actions that can be instantiated from a rule in this state.

        Parameters
        ----------
        rule :
            The rule to instantiate.
        mapping : optional
            An initial mapping to start from, constraining the possible instantiations.

        Returns
        -------
        The actions that can be instantiated from the rule in this state.
        """

        for assignment in self.all_assignments(rule, mapping):
            yield rule.instantiate(assignment)

    def all_assignments(self,
                        rule: Rule,
                        mapping: Mapping[Placeholder, Optional[Variable]] = None,
                        partial: bool = False,
                        allow_partial: Callable[[Placeholder], bool] = None,
                        ) -> Iterable[Mapping[Placeholder, Optional[Variable]]]:
        """
        Find all possible placeholder assignments that would allow a rule to be instantiated in this state.

        Parameters
        ----------
        rule :
            The rule to instantiate.
        mapping : optional
            An initial mapping to start from, constraining the possible instantiations.
        partial : optional
            Whether incomplete mappings, that would require new variables or propositions, are allowed.
        allow_partial : optional
            A callback function that returns whether a partial match may involve the given placeholder.

        Returns
        -------
        The possible mappings for instantiating the rule.  Partial mappings requiring new variables will have None in
        place of existing Variables.
        """

        if mapping is None:
            mapping = {}
        else:
            # Copy the input mapping so we can mutate it
            mapping = dict(mapping)

        used_vars = set(mapping.values())

        if partial:
            new_phs = [ph for ph in rule.placeholders if ph not in mapping]
            return self._all_assignments(new_phs, mapping, used_vars, True, allow_partial)
        else:
            # Precompute the new placeholders at every depth to avoid wasted work
            seen_phs = set(mapping.keys())
            new_phs_by_depth = []
            for pred in rule.preconditions:
                new_phs = []
                for ph in pred.parameters:
                    if ph not in seen_phs:
                        new_phs.append(ph)
                        seen_phs.add(ph)
                new_phs_by_depth.append(new_phs)

            # Placeholders uniquely found in postcondition are considered as free variables.
            free_vars = [ph for ph in rule.placeholders if ph not in seen_phs]
            new_phs_by_depth.append(free_vars)

            return self._all_applicable_assignments(rule, mapping, used_vars, new_phs_by_depth, 0)

    def _all_applicable_assignments(self,
                                    rule: Rule,
                                    mapping: Dict[Placeholder, Optional[Variable]],
                                    used_vars: Set[Variable],
                                    new_phs_by_depth: List[List[Placeholder]],
                                    depth: int,
                                    ) -> Iterable[Mapping[Placeholder, Optional[Variable]]]:
        """
        Find all assignments that would be applicable in this state.  We recurse through the rule's preconditions, at
        each level determining possible variable assignments from the current facts.
        """

        new_phs = new_phs_by_depth[depth]

        if depth >= len(rule.preconditions):
            # There are no applicability constraints on the free variables, so solve them unconstrained
            yield from self._all_assignments(new_phs, mapping, used_vars, False)
            return

        pred = rule.preconditions[depth]

        types = [self._logic.types.get(t) for t in pred.signature.types]
        for subtypes in self._logic.types.multi_subtypes(types):
            signature = Signature(pred.signature.name, [t.name for t in subtypes])
            for prop in self.facts_with_signature(signature):
                for ph, var in zip(pred.parameters, prop.arguments):
                    existing = mapping.get(ph)
                    if existing is None:
                        if var in used_vars:
                            break
                        mapping[ph] = var
                        used_vars.add(var)
                    elif existing != var:
                        break
                else:
                    yield from self._all_applicable_assignments(rule, mapping, used_vars, new_phs_by_depth, depth + 1)

                # Reset the mapping to what it was before the recursive call
                for ph in new_phs:
                    var = mapping.pop(ph, None)
                    used_vars.discard(var)

    def _all_assignments(self,
                         placeholders: List[Placeholder],
                         mapping: Dict[Placeholder, Variable],
                         used_vars: Set[Variable],
                         partial: bool,
                         allow_partial: Callable[[Placeholder], bool] = None,
                         ) -> Iterable[Mapping[Placeholder, Optional[Variable]]]:
        """
        Find all possible assignments of the given placeholders, without regard to whether any predicates match.
        """

        if allow_partial is None:
            allow_partial = lambda ph: True  # noqa: E731

        candidates = []
        for ph in placeholders:
            matched_vars = set()
            for type in self._logic.types.get(ph.type).subtypes:
                matched_vars |= self.variables_of_type(type.name)
            matched_vars -= used_vars
            if partial and allow_partial(ph):
                # Allow new variables to be created
                matched_vars.add(ph)
            candidates.append(list(matched_vars))

        for assignment in unique_product(*candidates):
            for ph, var in zip(placeholders, assignment):
                if var == ph:
                    mapping[ph] = None
                elif var not in used_vars:
                    mapping[ph] = var
                    used_vars.add(var)
                else:
                    # Distinct placeholders can't be assigned the same variable
                    break
            else:
                yield mapping.copy()

            for ph in placeholders:
                used_vars.discard(mapping.get(ph))

        for ph in placeholders:
            mapping.pop(ph, None)

    def copy(self) -> "State":
        """
        Create a copy of this state.
        """

        copy = State(self._logic)

        for k, v in self._facts.items():
            copy._facts[k] = v.copy()

        copy._vars_by_name = self._vars_by_name.copy()
        for k, v in self._vars_by_type.items():
            copy._vars_by_type[k] = v.copy()
        copy._var_counts = self._var_counts.copy()

        return copy

    def serialize(self) -> Sequence:
        """
        Serialize this state.
        """
        return [f.serialize() for f in self.facts]

    @classmethod
    def deserialize(cls, data: Sequence) -> "State":
        """
        Deserialize a `State` object from `data`.
        """
        return cls([Proposition.deserialize(d) for d in data])

    def __eq__(self, other):
        if isinstance(other, State):
            return set(self.facts) == set(other.facts)
        else:
            return NotImplemented

    def __str__(self):
        lines = ["State({"]

        for sig in sorted(self._facts.keys()):
            facts = self._facts[sig]
            if len(facts) == 0:
                continue

            lines.append("    {}: {{".format(sig))
            for fact in sorted(facts):
                lines.append("        {},".format(fact))
            lines.append("    },")

        lines.append("})")

        return "\n".join(lines)
