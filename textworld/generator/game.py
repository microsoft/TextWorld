# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import json

from typing import List, Dict, Optional, Mapping, Any
from collections import OrderedDict

from textworld.generator import data
from textworld.generator.text_grammar import Grammar
from textworld.generator.world import World
from textworld.logic import Action, Proposition, Rule, State
from textworld.generator.vtypes import VariableTypeTree
from textworld.generator.grammar import get_reverse_action
from textworld.generator.graph_networks import DIRECTIONS

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


class Quest:
    """ Quest presentation in TextWorld.

    A quest is a sequence of :py:class:`Action <textworld.logic.Action>`
    undertaken with a goal.
    """

    def __init__(self, actions: Optional[List[Action]],
                 winning_conditions: Optional[Collection[Proposition]] = None,
                 failing_conditions: Optional[Collection[Proposition]] = None,
                 desc: str = "") -> None:
        """
        Args:
            actions: The actions to be performed to complete the quest.
                     If `None`, then `winning_conditions` must be provided.
            winning_conditions: Set of propositions that need to be true
                                before marking the quest as completed.
                                Default: postconditions of the last action.
            failing_conditions: Set of propositions that if are all true
                                means the quest is failed.
                                Default: can't fail the quest.
            desc: A text description of the quest.
        """
        self.actions = actions
        self.desc = desc
        self.commands = []
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
            if self.actions is None:
                raise UnderspecifiedQuestError()

            # The default winning conditions are the postconditions of the
            # last action in the quest.
            winning_conditions = self.actions[-1].postconditions

        from textworld.utils import uniquify
        arguments = uniquify([a for c in winning_conditions for a in c.arguments])
        self.win_action = Action("win", winning_conditions, [Proposition("win", arguments)] + list(winning_conditions))
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
            self.fail_action = Action("fail", failing_conditions, [Proposition("fail")])

        return self.fail_action

    def __hash__(self) -> int:
        return hash((tuple(self.actions),
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
                 quests: Optional[List[Quest]] = None) -> None:
        """
        Args:
            world: The world to use for the game.
            quests: The quests to done in the game.
            grammar: The grammar to control the text generation.
        """
        self.world = world
        self.state = world.state.copy()  # Current state of the game.
        self.grammar = grammar
        self.quests = [] if quests is None else quests
        self.metadata = {}
        self._objective = None
        self._infos = self._build_infos()
        self._rules = data.get_rules()
        self._types = data.get_types()
        # TODO:
        # self.change_names()
        # self.change_descriptions()

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
        game = Game(self.world, self.grammar, self.quests)
        game._infos = self.infos
        game.state = self.state.copy()
        game._rules = self._rules
        game._types = self._types
        game._objective = self._objective
        return game

    def change_grammar(self, grammar: Grammar) -> None:
        """ Changes the grammar used and regenerate all text. """
        from textworld.generator import inform7
        from textworld.generator.text_generation import generate_text_from_grammar
        self.grammar = grammar
        generate_text_from_grammar(self, self.grammar)
        for quest in self.quests:
            # TODO: should have a generic way of generating text commands from actions
            #       insteaf of relying on inform7 convention.
            quest.commands = inform7.gen_commands_from_actions(quest.actions, self.infos)

        # TODO
        # self.change_names()
        # self.change_descriptions()

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
        grammar = None
        if "grammar" in data:
            grammar = Grammar(data["grammar"])
        quests = [Quest.deserialize(d) for d in data["quests"]]
        game = cls(world, grammar, quests)
        game._infos = {k: EntityInfo.deserialize(v)
                       for k, v in data["infos"]}
        game.state = State.deserialize(data["state"])
        game._rules = {k: Rule.deserialize(v)
                       for k, v in data["rules"]}
        game._types = VariableTypeTree.deserialize(data["types"])
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
            data["grammar"] = self.grammar.flags
        data["quests"] = [quest.serialize() for quest in self.quests]
        data["infos"] = [(k, v.serialize()) for k, v in self._infos.items()]
        data["rules"] = [(k, v.serialize()) for k, v in self._rules.items()]
        data["types"] = self._types.serialize()
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
        return sorted(self._types.types)

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
        commands = [data.INFORM7_COMMANDS[rule_name]
                    for rule_name in self._rules]
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
        
        # We assume the last quest includes all actions needed to solve the game.
        return self.quests[-1].desc 

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
            can mutually removed information needed by the other.   
        """
        return len(other.action.removed & self.action._pre_set) > 0

    def __str__(self) -> str:
        params = ", ".join(map(str, self.action.variables))
        return "{}({})".format(self.action.name, params)


class ActionDependencyTree(DependencyTree):

    def pop(self, action: Action) -> Optional[Action]:
        super().pop(action)

        reverse_action = None
        # The last action might have impacted one of the subquests.
        reverse_action = get_reverse_action(action)
        if reverse_action is not None:
            self.push(reverse_action)

        return reverse_action

    def tolist(self) -> Optional[List[Action]]:
        """ Builds a list with the actions contained in this dependency tree.

        The list is greedily built by iteratively popping leaves from
        the dependency tree.
        """
        tree = self.copy()  # Make a copy of the tree to work on.

        actions = []
        last_reverse_action = None
        while len(tree.roots) > 0:
            # Try leaves that doesn't affect the others first.
            for leaf in sorted(tree.leaves_elements):
                if leaf.action != last_reverse_action:
                    break  # Choose an action that avoids cycles.

            actions.append(leaf.action)
            last_reverse_action = tree.pop(leaf.action)

        return actions
    
    def compress(self):
        tree = ActionDependencyTree(element_type=ActionDependencyTreeElement)
        for action in self.tolist()[::-1]:
            tree.push(action)
        
        self.roots = tree.roots


class QuestProgression:
    """ QuestProgression keeps track of the completion of a quest.

    Internally, the quest is represented as a dependency tree of
    relevant actions to be performed.
    """

    def __init__(self, quest: Quest) -> None:
        """
        Args:
            quest: The quest to keep track of its completion.
        """
        self._quest = quest
        self._winning_policy = None

        # Build a tree representation of the quest.
        self._tree = ActionDependencyTree(element_type=ActionDependencyTreeElement)
        self._tree.push(quest.win_action)
        for action in quest.actions[::-1]:
            self._tree.push(action)

        # We compress the tree since quest's actions might not be optimal.
        # e.g. go west > go east > go west cycles
        self._tree.compress()
        self._rebuild_policy()
                
    def _rebuild_policy(self):
        self._winning_policy = None
        if self._tree is not None:
            self._winning_policy = self._tree.tolist()
    
    @property
    def winning_policy(self) -> List[Action]:
        """ Actions to be performed in order to complete the quest. """
        if self._winning_policy is None:
            return None

        return self._winning_policy[:-1]  # Discard "win" action.

    @property
    def done(self):
        """ Check whether the quest is done. """
        if self.winning_policy is None:
            return True
            
        return len(self.winning_policy) == 0

    def is_completed(self, state: State) -> bool:
        """ Check whether the quest is completed. """
        return state.is_applicable(self._quest.win_action)

    def has_failed(self, state: State) -> bool:
        """ Check whether the quest has failed. """
        if self._quest.fail_action is None:
            return False

        return state.is_applicable(self._quest.fail_action)

    def update(self, action: Action) -> None:
        """ Update the state of the quest after a given action was performed.

        Args:
            action: Action affecting the state of the quest.
        """
        # Determine if we moved away from the goal or closer to it.
        if action in self._tree.leaves_values:
            # The last action was meaningful for the quest.
            self._tree.pop(action)
        else:
            # The last action must have moved us away from the goal.
            # We need to reverse it.
            reverse_action = get_reverse_action(action)
            if reverse_action is None:
                # Irreversible action.
                self._tree = None  # Can't track quest anymore.
            else:
                self._tree.push(reverse_action)

        self._rebuild_policy()

    def compress_winning_policy(self, state: State):
        for j in range(0, len(self._winning_policy)):
            for i in range(j + 1, len(self._winning_policy))[::-1]:                    
                if state.is_sequence_applicable(self._winning_policy[:j] + self._winning_policy[i:]):
                    for action in self._winning_policy[:i]:
                        self._tree.pop(action)
                    
                    for action in self._winning_policy[:j][::-1]:
                        self._tree.push(action)
                    
                    self._rebuild_policy()
                    return True

        return False


class GameProgression:
    """ GameProgression keeps track of the progression of a game.

    If `tracking_quest` is  True, then `winning_policy` will be the list
    of Action that need to be applied in order to complete the game.
    """

    def __init__(self, game: Game, track_quest: bool = True) -> None:
        """
        Args:
            game: The gaquest_progressionogression of.
            track_quest:quest_progressionould track the quest completion.
        """
        self.game = game
        self.state = game.state.copy()
        self._valid_actions = list(self.state.all_applicable_actions(self.game._rules.values(),
                                                                     self.game._types.constants_mapping))
        self.quest_progressions = None
        if track_quest and len(game.quests) > 0:
            self.quest_progressions = [QuestProgression(quest) for quest in game.quests]
            for quest_progression in self.quest_progressions:
                while quest_progression.compress_winning_policy(self.state):
                    pass

    @property
    def done(self) -> bool:
        """ Whether the quest is completed or has failed. """
        if self.quest_progressions is None:
            return False

        all_completed = True
        for quest_progression in self.quest_progressions:
            if quest_progression.has_failed(self.state):
                return True

            all_completed &= quest_progression.done

        return all_completed

    @property
    def tracking_quest(self) -> bool:
        """ Whether the quest is tracked or not. """
        return self.quest_progressions is not None

    @property
    def valid_actions(self) -> List[Action]:
        """ Actions that are valid at the current state. """
        return self._valid_actions

    @property
    def winning_policy(self) -> Optional[List[Action]]:
        """ Actions to be performed in order to complete the game.

        Returns:
            A policy that leads to winning the game. It can be `None`
            if `tracking_quest` is `False` or the quest has failed.
        """
        if not self.tracking_quest:
            return None
        
        # Check if any quest has failed.
        if any(quest_progression.winning_policy is None for quest_progression in self.quest_progressions):
            return None
        
        # Greedily build a new winning policy by merging all individual quests' tree.
        trees = [qp._tree for qp in self.quest_progressions if not qp.done]
        master_quest_tree = ActionDependencyTree(element_type=ActionDependencyTreeElement,
                                                 trees=trees)
        
        # print(master_quest_tree)
        winning_policy = master_quest_tree.tolist()
        return [a for a in winning_policy if a.name != "win"]

    def update(self, action: Action) -> None:
        """ Update the state of the game given the provided action.

        Args:
            action: Action affecting the state of the game.
        """
        # Update world facts.
        self.state.apply(action)

        # Get valid actions.
        self._valid_actions = list(self.state.all_applicable_actions(self.game._rules.values(),
                                                                     self.game._types.constants_mapping))

        if self.tracking_quest:
            if self.state.is_sequence_applicable(self.winning_policy):
                pass  # The last action didn't impact the quest.
            else:
                for quest_progression in self.quest_progressions:
                    if quest_progression.done:
                        continue
                    
                    # Try compressing the winning policy for the quest, 
                    # otherwise update its progression given the new action.
                    if not quest_progression.compress_winning_policy(self.state):
                        quest_progression.update(action)
