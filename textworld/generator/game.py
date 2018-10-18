# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import copy
import json

from typing import List, Dict, Optional, Mapping, Any, Iterable, Union
from collections import OrderedDict

from numpy.random import RandomState

from textworld import g_rng
from textworld.utils import encode_seeds
from textworld.generator.data import KnowledgeBase
from textworld.generator.text_grammar import Grammar, GrammarOptions
from textworld.generator.world import World
from textworld.logic import Action, Proposition, Rule, State
from textworld.generator.vtypes import VariableTypeTree
from textworld.generator.graph_networks import DIRECTIONS

from textworld.generator.chaining import ChainingOptions

from textworld.generator.dependency_tree import DependencyTree
from textworld.generator.dependency_tree import DependencyTreeElement


try:
    from typing import Collection
except ImportError:
    # Collection is new in Python 3.6 -- fall back on Iterable for 3.5
    from typing import Iterable as Collection


class UnderspecifiedQuestError(NameError):
    def __init__(self):
        msg = "Either the list of actions or the win_condition  he quest must have "
        super().__init__(msg)


def gen_commands_from_actions(actions: Iterable[Action], kb: Optional[KnowledgeBase] = None) -> List[str]:
    kb = kb or KnowledgeBase.default()
    def _get_name_mapping(action):
        mapping = kb.rules[action.name].match(action)
        return {ph.name: var.name for ph, var in mapping.items()}

    commands = []
    for action in actions:
        command = "None"
        if action is not None:
            command = kb.inform7_commands[action.name]
            command = command.format(**_get_name_mapping(action))

        commands.append(command)

    return commands


class Quest:
    """ Quest presentation in TextWorld.

    A quest is a sequence of :py:class:`Action <textworld.logic.Action>`
    undertaken with a goal.
    """

    def __init__(self, actions: Optional[Iterable[Action]] = None,
                 winning_conditions: Optional[Collection[Proposition]] = None,
                 failing_conditions: Optional[Collection[Proposition]] = None,
                 desc: Optional[str] = None) -> None:
        """
        Args:
            actions: The actions to be performed to complete the quest.
                     If `None` or an empty list, then `winning_conditions`
                     must be provided.
            winning_conditions: Set of propositions that need to be true
                                before marking the quest as completed.
                                Default: postconditions of the last action.
            failing_conditions: Set of propositions that if are all true
                                means the quest is failed.
                                Default: can't fail the quest.
            desc: A text description of the quest.
        """
        self.actions = tuple(actions) if actions else ()
        self.desc = desc
        self.commands = gen_commands_from_actions(self.actions)
        self.reward = 1
        self.win_action = self.set_winning_conditions(winning_conditions)
        self.fail_action = self.set_failing_conditions(failing_conditions)

    def set_winning_conditions(self, winning_conditions: Optional[Collection[Proposition]]) -> Action:
        """ Sets wining conditions for this quest.

        Args:
            winning_conditions: Set of propositions that need to be true
                                before marking the quest as completed.
                                Default: postconditions of the last action.
        Returns:
            An action that is only applicable when the quest is finished.
        """
        if winning_conditions is None:
            if len(self.actions) == 0:
                raise UnderspecifiedQuestError()

            # The default winning conditions are the postconditions of the
            # last action in the quest.
            winning_conditions = self.actions[-1].postconditions

        # TODO: Make win propositions distinguishable by adding arguments?
        win_fact = Proposition("win")
        self.win_action = Action("win", preconditions=winning_conditions,
                                        postconditions=list(winning_conditions) + [win_fact])
        return self.win_action

    def set_failing_conditions(self, failing_conditions: Optional[Collection[Proposition]]) -> Optional[Action]:
        """ Sets the failing conditions of this quest.

        Args:
            failing_conditions: Set of propositions that if are all true
                                means the quest is failed.
                                Default: can't fail the quest.
        Returns:
            An action that is only applicable when the quest has failed or `None`
            if the quest can be failed.
        """
        self.fail_action = None
        if failing_conditions is not None:
            # TODO: Make fail propositions distinguishable by adding arguments?
            fail_fact = Proposition("fail")
            self.fail_action = Action("fail", preconditions=failing_conditions,
                                              postconditions=list(failing_conditions) + [fail_fact])

        return self.fail_action

    def __hash__(self) -> int:
        return hash((self.actions,
                     self.win_action,
                     self.fail_action,
                     self.desc,
                     tuple(self.commands)))

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Quest) and
                self.actions == other.actions and
                self.win_action == other.win_action and
                self.fail_action == other.fail_action and
                self.desc == other.desc and
                self.reward == other.reward and
                self.commands == other.commands)

    @classmethod
    def deserialize(cls, data: Mapping) -> "Quest":
        """ Creates a `Quest` from serialized data.

        Args:
            data: Serialized data with the needed information to build a
                  `Quest` object.
        """
        actions = [Action.deserialize(d) for d in data["actions"]]
        win_action = Action.deserialize(data["win_action"])
        failing_conditions = None
        if data["fail_action"] is not None:
            fail_action = Action.deserialize(data["fail_action"])
            failing_conditions = fail_action.preconditions

        desc = data["desc"]
        quest = cls(actions, win_action.preconditions, failing_conditions, desc=desc)
        quest.commands = data["commands"]
        quest.reward = data.get("reward", 1)
        return quest

    def serialize(self) -> Mapping:
        """ Serialize this quest.

        Results:
            Quest's data serialized to be JSON compatible
        """
        data = {}
        data["desc"] = self.desc
        data["reward"] = self.reward
        data["commands"] = self.commands
        data["actions"] = [action.serialize() for action in self.actions]
        data["win_action"] = self.win_action.serialize()
        data["fail_action"] = self.fail_action
        if self.fail_action is not None:
            data["fail_action"] = self.fail_action.serialize()

        return data

    def copy(self) -> "Quest":
        """ Copy this quest. """
        return self.deserialize(self.serialize())

    def __str__(self) -> str:
        return " -> ".join(map(str, self.actions))

    def __repr__(self) -> str:
        txt = "Quest({!r}, winning_conditions={!r}, failing_conditions={!r} desc={!r})"
        failing_conditions = None
        if self.fail_action is not None:
            failing_conditions = self.fail_action.preconditions

        return txt.format(self.actions, self.win_action.preconditions,
                          failing_conditions, self.desc)


class EntityInfo:
    """ Additional information about entities in the game. """
    __slots__ = ['id', 'type', 'name', 'noun', 'adj', 'desc', 'room_type']

    def __init__(self, id: str, type: str) -> None:
        #: str: Unique name for this entity. It is used when generating
        self.id = id
        #: str: The type of this entity.
        self.type = type
        #: str: The name that will be displayed in-game to identify this entity.
        self.name = None
        #: str: The noun part of the name, if available.
        self.noun = None
        #: str: The adjective (i.e. descriptive) part of the name, if available.
        self.adj = None
        #: str: Text description displayed when examining this entity in the game.
        self.desc = None
        #: str: Type of the room this entity belongs to. It used to influence
        #:      its `name` during text generation.
        self.room_type = None

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, EntityInfo) and
                all(getattr(self, slot) == getattr(other, slot)
                    for slot in self.__slots__))

    def __hash__(self) -> int:
        return hash(tuple(getattr(self, slot) for slot in self.__slots__))

    def __str__(self) -> str:
        return "Info({}: {} | {})".format(self.name, self.adj, self.noun)

    @classmethod
    def deserialize(cls, data: Mapping) -> "EntityInfo":
        """ Creates a `EntityInfo` from serialized data.

        Args:
            data: Serialized data with the needed information to build a
                  `EntityInfo` object.
        """
        info = cls(data["id"], data["type"])
        for slot in cls.__slots__:
            setattr(info, slot, data[slot])

        return info

    def serialize(self) -> Mapping:
        """ Serialize this object.

        Results:
            EntityInfo's data serialized to be JSON compatible
        """
        return {slot: getattr(self, slot) for slot in self.__slots__}


class Game:
    """ Game representation in TextWorld.

    A `Game` is defined by a world and it can have quest(s) or not.
    Additionally, a grammar can be provided to control the text generation.
    """

    def __init__(self, world: World, grammar: Optional[Grammar] = None,
                 quests: Optional[List[Quest]] = None,
                 kb: Optional[KnowledgeBase] = None) -> None:
        """
        Args:
            world: The world to use for the game.
            quests: The quests to done in the game.
            grammar: The grammar to control the text generation.
        """
        self.world = world
        self.state = world.state.copy()  # Current state of the game.
        self.quests = [] if quests is None else quests
        self.metadata = {}
        self._objective = None
        self._infos = self._build_infos()
        self.kb = kb or KnowledgeBase.default()
        self.change_grammar(grammar)

        self._main_quest = None

    @property
    def main_quest(self):
        if self._main_quest is None:
            from textworld.generator.inform7 import Inform7Game
            from textworld.generator.text_generation import assign_description_to_quest
            inform7 = Inform7Game(self)
            self._main_quest = Quest(actions=GameProgression(self).winning_policy)
            self._main_quest.desc = assign_description_to_quest(self._main_quest, self, self.grammar)
            self._main_quest.commands = inform7.gen_commands_from_actions(self._main_quest.actions)

        return self._main_quest

    @property
    def infos(self) -> Dict[str, EntityInfo]:
        """ Information about the entities in the game. """
        return self._infos

    def _build_infos(self) -> Dict[str, EntityInfo]:
        mapping = OrderedDict()
        for entity in self.world.entities:
            if entity not in mapping:
                mapping[entity.id] = EntityInfo(entity.id, entity.type)

        return mapping

    def copy(self) -> "Game":
        """ Make a shallow copy of this game. """
        game = Game(self.world, self.grammar, self.quests, self.kb)
        game._infos = self.infos
        game.state = self.state.copy()
        game.kb = self.kb
        game._objective = self._objective
        return game

    def change_grammar(self, grammar: Grammar) -> None:
        """ Changes the grammar used and regenerate all text. """
        self.grammar = grammar
        if self.grammar is None:
            return

        from textworld.generator.inform7 import Inform7Game
        from textworld.generator.text_generation import generate_text_from_grammar
        inform7 = Inform7Game(self)

        generate_text_from_grammar(self, self.grammar)
        for quest in self.quests:
            # TODO: should have a generic way of generating text commands from actions
            #       instead of relying on inform7 convention.
            quest.commands = inform7.gen_commands_from_actions(quest.actions)

    def save(self, filename: str) -> None:
        """ Saves the serialized data of this game to a file. """
        with open(filename, 'w') as f:
            json.dump(self.serialize(), f)

    @classmethod
    def load(cls, filename: str) -> "Game":
        """ Creates `Game` from serialized data saved in a file. """
        with open(filename, 'r') as f:
            return cls.deserialize(json.load(f))

    @classmethod
    def deserialize(cls, data: Mapping) -> "Game":
        """ Creates a `Game` from serialized data.

        Args:
            data: Serialized data with the needed information to build a
                  `Game` object.
        """
        world = World.deserialize(data["world"])
        game = cls(world)
        if "grammar" in data:
            game.grammar = Grammar(data["grammar"])

        game.quests = [Quest.deserialize(d) for d in data["quests"]]
        game._infos = {k: EntityInfo.deserialize(v)
                       for k, v in data["infos"]}
        game.state = State.deserialize(data["state"])
        game.kb = KnowledgeBase.deserialize(data["KB"])
        game.metadata = data.get("metadata", {})
        game._objective = data.get("objective", None)

        return game

    def serialize(self) -> Mapping:
        """ Serialize this object.

        Results:
            Game's data serialized to be JSON compatible
        """
        data = {}
        data["world"] = self.world.serialize()
        data["state"] = self.state.serialize()
        if self.grammar is not None:
            data["grammar"] = self.grammar.options.serialize()
        data["quests"] = [quest.serialize() for quest in self.quests]
        data["infos"] = [(k, v.serialize()) for k, v in self._infos.items()]
        data["KB"] = self.kb.serialize()
        data["metadata"] = self.metadata
        data["objective"] = self._objective
        return data

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Game) and
                self.world == other.world and
                self.infos == other.infos and
                self.quests == other.quests and
                self._objective == other._objective)

    def __hash__(self) -> int:
        state = (self.world,
                 frozenset(self.quests),
                 frozenset(self.infos.items()),
                 self._objective)

        return hash(state)

    @property
    def directions_names(self) -> List[str]:
        return DIRECTIONS

    @property
    def objects_types(self) -> List[str]:
        """ All types of objects in this game. """
        return sorted(self.kb.types.types)

    @property
    def objects_names(self) -> List[str]:
        """ The names of all relevant objects in this game. """
        def _filter_unnamed_and_room_entities(e):
            return e.name is not None and e.type != "r"

        entities_infos = filter(_filter_unnamed_and_room_entities, self.infos.values())
        return [info.name for info in entities_infos]

    @property
    def objects_names_and_types(self) -> List[str]:
        """ The names of all non-player objects along with their type in this game. """
        def _filter_unnamed_and_room_entities(e):
            return e.name is not None and e.type != "r"

        entities_infos = filter(_filter_unnamed_and_room_entities, self.infos.values())
        return [(info.name, info.type) for info in entities_infos]

    @property
    def verbs(self) -> List[str]:
        """ Verbs that should be recognized in this game. """
        # Retrieve commands templates for every rule.
        commands = [self.kb.inform7_commands[rule_name]
                    for rule_name in self.kb.rules]
        verbs = [cmd.split()[0] for cmd in commands]
        verbs += ["look", "inventory", "examine", "wait"]
        return sorted(set(verbs))

    @property
    def win_condition(self) -> List[Collection[Proposition]]:
        """ All win conditions, one for each quest. """
        return [q.winning_conditions for q in self.quests]

    @property
    def objective(self) -> str:
        if self._objective is not None:
            return self._objective

        if len(self.quests) == 0:
            return ""

        self._objective = self.main_quest.desc
        return self._objective

    @objective.setter
    def objective(self, value: str):
        self._objective = value


class ActionDependencyTreeElement(DependencyTreeElement):
    """ Representation of an `Action` in the dependency tree.

    The notion of dependency and ordering is defined as follows:

    * action1 depends on action2 if action1 needs the propositions
      added by action2;
    * action1 should be performed before action2 if action2 removes
      propositions needed by action1.
    """

    def depends_on(self, other: "ActionDependencyTreeElement") -> bool:
        """ Check whether this action depends on the `other`.

        Action1 depends on action2 when the intersection between
        the propositions added by action2 and the preconditions
        of the action1 is not empty, i.e. action1 needs the
        propositions added by action2.
        """
        return len(other.action.added & self.action._pre_set) > 0

    @property
    def action(self) -> Action:
        return self.value

    def is_distinct_from(self, others: List["ActionDependencyTreeElement"]) -> bool:
        """
        Check whether this element is distinct from `others`.

        We check if self.action has any additional information
        that `others` actions don't have. This helps us to
        identify whether a group of nodes in the dependency tree
        already contain all the needed information that self.action
        would bring.
        """
        new_facts = set(self.action.added)
        for other in others:
            new_facts -= other.action.added

        return len(new_facts) > 0

    def __lt__(self, other: "ActionDependencyTreeElement") -> bool:
        """ Order ActionDependencyTreeElement elements.

        Actions that remove information needed by other actions
        should be sorted further in the list.

        Notes:
            This is not a proper ordering, i.e. two actions
            can mutually removed information needed by each other.
        """
        def _required_facts(node):
            pre_set = set(node.action._pre_set)
            while node.parent is not None:
                pre_set |= node.parent.action._pre_set
                pre_set -= node.action.added
                node = node.parent

            return pre_set

        return len(other.action.removed & _required_facts(self)) > len(self.action.removed & _required_facts(other))

    def __str__(self) -> str:
        params = ", ".join(map(str, self.action.variables))
        return "{}({})".format(self.action.name, params)


class ActionDependencyTree(DependencyTree):

    def __init__(self, *args, kb: Optional[KnowledgeBase] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._kb = kb or KnowledgeBase.default()

    def remove(self, action: Action) -> Optional[Action]:
        super().remove(action)

        # The last action might have impacted one of the subquests.
        reverse_action = self._kb.get_reverse_action(action)
        if reverse_action is not None:
            self.push(reverse_action)

        return reverse_action

    def flatten(self) -> Iterable[Action]:
        """
        Generates a flatten representation of this dependency tree.

        Actions are greedily yielded by iteratively popping leaves from
        the dependency tree.
        """
        tree = self.copy()  # Make a copy of the tree to work on.
        last_reverse_action = None
        while len(tree.roots) > 0:
            # Use 'sort' to try leaves that doesn't affect the others first.
            for leaf in sorted(tree.leaves_elements):
                if leaf.action != last_reverse_action:
                    break  # Choose an action that avoids cycles.

            yield leaf.action
            last_reverse_action = tree.remove(leaf.action)

    def copy(self) -> "ActionDependencyTree":
        tree = super().copy()
        tree._kb = self._kb
        return tree


class QuestProgression:
    """ QuestProgression keeps track of the completion of a quest.

    Internally, the quest is represented as a dependency tree of
    relevant actions to be performed.
    """

    def __init__(self, quest: Quest, kb: KnowledgeBase) -> None:
        """
        Args:
            quest: The quest to keep track of its completion.
        """
        self._kb = kb or KnowledgeBase.default()
        self.quest = quest
        self._completed = False
        self._failed = False
        self._unfinishable = False

        # Build a tree representation of the quest.
        self._tree = ActionDependencyTree(kb=self._kb,
                                          element_type=ActionDependencyTreeElement)
        self._tree.push(quest.win_action)
        for action in quest.actions[::-1]:
            self._tree.push(action)

        self._winning_policy = quest.actions + (quest.win_action,)

    @property
    def winning_policy(self) -> List[Action]:
        """ Actions to be performed in order to complete the quest. """
        if self.done:
            return []

        return self._winning_policy[:-1]  # Discard "win" action.

    @property
    def done(self) -> bool:
        """ Check if the quest is done (i.e. completed, failed or unfinishable). """
        return self.completed or self.failed or self.unfinishable

    @property
    def completed(self) -> bool:
        """ Check whether the quest is completed. """
        return self._completed

    @property
    def failed(self) -> bool:
        """ Check whether the quest has failed. """
        return self._failed

    @property
    def unfinishable(self) -> bool:
        """ Check whether the quest is in an unfinishable state. """
        return self._unfinishable

    def update(self, action: Optional[Action] = None, state: Optional[State] = None) -> None:
        """ Update quest progression given available information.

        Args:
            action: Action potentially affecting the quest progression.
            state: Current game state.
        """
        if self.done:
            return  # Nothing to do, the quest is already done.

        if state is not None:
            # Check if quest is completed.
            if self.quest.win_action is not None:
                self._completed = state.is_applicable(self.quest.win_action)

            # Check if quest has failed.
            if self.quest.fail_action is not None:
                self._failed = state.is_applicable(self.quest.fail_action)

            # Try compressing the winning policy given the new game state.
            if self.compress_winning_policy(state):
                return  # A shorter winning policy has been found.

        if action is not None:
            # Determine if we moved away from the goal or closer to it.
            reverse_action = self._tree.remove(action)
            if reverse_action is None:  # Irreversible action.
                self._unfinishable = True  # Can't track quest anymore.

            self._winning_policy = tuple(self._tree.flatten())  # Rebuild policy.

    def compress_winning_policy(self, state: State) -> bool:
        """ Compress the winning policy given a game state.

        Args:
            state: Current game state.

        Returns:
            Whether the winning policy was compressed or not.
        """

        def _find_shorter_policy(policy):
            for j in range(0, len(policy)):
                for i in range(j + 1, len(policy))[::-1]:
                    shorter_policy = policy[:j] + policy[i:]
                    if state.is_sequence_applicable(shorter_policy):
                        self._tree = ActionDependencyTree(kb=self._kb,
                                                          element_type=ActionDependencyTreeElement)
                        for action in shorter_policy[::-1]:
                            self._tree.push(action)

                        return shorter_policy

            return None

        compressed = False
        policy = _find_shorter_policy(self._winning_policy)
        while policy is not None:
            compressed = True
            self._winning_policy = policy
            policy = _find_shorter_policy(policy)

        return compressed


class GameProgression:
    """ GameProgression keeps track of the progression of a game.

    If `tracking_quests` is  True, then `winning_policy` will be the list
    of Action that need to be applied in order to complete the game.
    """

    def __init__(self, game: Game, track_quests: bool = True) -> None:
        """
        Args:
            game: The game for which to track progression.
            track_quests: whether quest progressions are being tracked.
        """
        self.game = game
        self.state = game.state.copy()
        self._valid_actions = list(self.state.all_applicable_actions(self.game.kb.rules.values(),
                                                                     self.game.kb.types.constants_mapping))

        self.quest_progressions = []
        if track_quests:
            self.quest_progressions = [QuestProgression(quest, game.kb) for quest in game.quests]
            for quest_progression in self.quest_progressions:
                quest_progression.update(action=None, state=self.state)

    @property
    def done(self) -> bool:
        """ Whether all quests are completed or at least one has failed or is unfinishable. """
        return self.completed or self.failed

    @property
    def completed(self) -> bool:
        """ Whether all quests are completed. """
        if not self.tracking_quests:
            return False  # There is nothing to be "completed".

        return all(qp.completed for qp in self.quest_progressions)

    @property
    def failed(self) -> bool:
        """ Whether at least one quest has failed or is unfinishable. """
        if not self.tracking_quests:
            return False  # There is nothing to be "failed".

        return any((qp.failed or qp.unfinishable) for qp in self.quest_progressions)

    @property
    def score(self) -> int:
        """ Sum of the reward of all completed quests. """
        return sum(qp.quest.reward for qp in self.quest_progressions if qp.completed)

    @property
    def max_score(self) -> int:
        """ Sum of the reward of all quests. """
        return sum(quest.reward for quest in self.game.quests)

    @property
    def tracking_quests(self) -> bool:
        """ Whether quests are being tracked or not. """
        return len(self.quest_progressions) > 0

    @property
    def valid_actions(self) -> List[Action]:
        """ Actions that are valid at the current state. """
        return self._valid_actions

    @property
    def winning_policy(self) -> Optional[List[Action]]:
        """ Actions to be performed in order to complete the game.

        Returns:
            A policy that leads to winning the game. It can be `None`
            if `tracking_quests` is `False` or the quest has failed.
        """
        if not self.tracking_quests:
            return None

        # Check if any quest has failed.
        if any(quest.failed or quest.unfinishable for quest in self.quest_progressions):
            return None

        # Greedily build a new winning policy by merging all individual quests' tree.
        trees = [quest._tree for quest in self.quest_progressions if not quest.done]
        master_quest_tree = ActionDependencyTree(kb=self.game.kb,
                                                 element_type=ActionDependencyTreeElement,
                                                 trees=trees)

        return tuple(a for a in master_quest_tree.flatten() if a.name != "win")

    def update(self, action: Action) -> None:
        """ Update the state of the game given the provided action.

        Args:
            action: Action affecting the state of the game.
        """
        # Update world facts.
        self.state.apply(action)

        # Get valid actions.
        self._valid_actions = list(self.state.all_applicable_actions(self.game.kb.rules.values(),
                                                                     self.game.kb.types.constants_mapping))

        # Update all quest progressions given the last action and new state.
        for quest_progression in self.quest_progressions:
            quest_progression.update(action, self.state)


class GameOptions:
    """
    Options for customizing the game generation.

    Attributes:
        nb_rooms:
            Number of rooms in the game.
        nb_objects:
            Number of objects in the game.
        quest_length:
            Minimum number of actions the quest requires to be completed.
        quest_breadth:
            Control how nonlinear a quest can be (1: linear).
        games_dir:
            Path to the directory where the game will be saved.
        force_recompile:
            If `True`, recompile game even if it already exists.
        file_type:
            Type of the generated game file. Either .z8 (Z-Machine) or .ulx (Glulx).
        seeds:
            Seeds for the different generation processes.

               * If `None`, seeds will be sampled from
                 :py:data:`textworld.g_rng <textworld.utils.g_rng>`.
               * If `int`, it acts as a seed for a random generator that will be
                 used to sample the other seeds.
               * If dict, the following keys can be set:

                 * `'map'`: control the map generation;
                 * `'objects'`: control the type of objects and their
                   location;
                 * `'quest'`: control the quest generation;
                 * `'grammar'`: control the text generation.

                 For any key missing, a random number gets assigned (sampled
                 from :py:data:`textworld.g_rng <textworld.utils.g_rng>`).
        kb:
            The knowledge base containing the logic and the text grammars (see
            :py:class:`textworld.generator.KnowledgeBase <textworld.generator.data.KnowledgeBase>`
            for more information).
        chaining:
            For customizing the quest generation (see
            :py:class:`textworld.generator.ChainingOptions <textworld.generator.chaining.ChainingOptions>`
            for the list of available options).
        grammar:
            For customizing the text generation (see
            :py:class:`textworld.generator.GrammarOptions <textworld.generator.text_grammar.GrammarOptions>`
            for the list of available options).
    """

    def __init__(self):
        self.chaining = ChainingOptions()
        self.grammar = GrammarOptions()
        self._kb = None
        self._seeds = None

        self.nb_rooms = 1
        self.nb_objects = 1
        self.quest_length = 1
        self.quest_breadth = 1
        self.force_recompile = False

    @property
    def quest_length(self) -> int:
        return self.chaining.max_depth

    @quest_length.setter
    def quest_length(self, value: int) -> None:
        self.chaining.min_depth = 1
        self.chaining.max_depth = value

    @property
    def quest_breadth(self) -> int:
        return self.chaining.max_breadth

    @quest_breadth.setter
    def quest_breadth(self, value: int) -> None:
        self.chaining.min_breadth = 1
        self.chaining.max_breadth = value

    @property
    def seeds(self):
        return self._seeds

    @seeds.setter
    def seeds(self, value: Union[int, Mapping[str, int]]) -> None:
        keys = ['map', 'objects', 'quest', 'grammar']

        def _key_missing(seeds):
            return not set(seeds.keys()).issuperset(keys)

        seeds = value
        if type(value) is int:
            rng = RandomState(value)
            seeds = {}
        elif _key_missing(value):
            rng = g_rng.next()

        # Check if we need to generate missing seeds.
        self._seeds = {}
        for key in keys:
            if key in seeds:
                self._seeds[key] = seeds[key]
            else:
                self._seeds[key] = rng.randint(65635)

    @property
    def rngs(self) -> Dict[str, RandomState]:
        rngs = {}
        for key, seed in self._seeds.items():
            rngs[key] = RandomState(seed)

        return rngs

    @property
    def kb(self) -> KnowledgeBase:
        if self._kb is None:
            self.kb = KnowledgeBase.load()

        return self._kb

    @kb.setter
    def kb(self, value: KnowledgeBase) -> None:
        self._kb = value
        self.chaining.logic = self._kb.logic
        self.chaining.fixed_mapping = self._kb.types.constants_mapping

    def copy(self) -> "GameOptions":
        return copy.copy(self)

    @property
    def uuid(self) -> str:
        # TODO: generate uuid from chaining options?
        uuid = "tw-game-{specs}-{grammar}-{seeds}"
        uuid = uuid.format(specs=encode_seeds((self.nb_rooms, self.nb_objects, self.quest_length, self.quest_breadth)),
                           grammar=self.grammar.uuid,
                           seeds=encode_seeds([self.seeds[k] for k in sorted(self._seeds)]))
        return uuid
