# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from os.path import join as pjoin
from collections import OrderedDict

from typing import List, Iterable, Union, Optional

import networkx as nx
import numpy as np

import textworld

from textworld.core import EnvInfos
from textworld.utils import make_temp_directory

from textworld.generator import Grammar
from textworld.generator.graph_networks import direction
from textworld.generator.data import KnowledgeBase
from textworld.generator.vtypes import get_new
from textworld.logic import State, Variable, Proposition, Action
from textworld.generator.game import GameOptions
from textworld.generator.game import Game, World, Quest, Event, EntityInfo
from textworld.generator.graph_networks import DIRECTIONS
from textworld.render import visualize
from textworld.envs.wrappers import Recorder


def get_failing_constraints(state, kb: Optional[KnowledgeBase] = None):
    kb = kb or KnowledgeBase.default()
    fail = Proposition("fail", [])

    failed_constraints = []
    constraints = state.all_applicable_actions(kb.constraints.values())
    for constraint in constraints:
        if state.is_applicable(constraint):
            # Optimistically delay copying the state
            copy = state.copy()
            copy.apply(constraint)

            if copy.is_fact(fail):
                failed_constraints.append(constraint)

    return failed_constraints


class MissingPlayerError(ValueError):
    pass


class ExitAlreadyUsedError(ValueError):
    pass


class PlayerAlreadySetError(ValueError):
    pass


class QuestError(ValueError):
    pass


class FailedConstraintsError(ValueError):
    """
    Thrown when a constraint has failed during generation.
    """

    def __init__(self, failed_constraints: List[Action]) -> None:
        """
        Args:
            failed_constraints: The constraints that have failed
        """
        msg = "The following constraints have failed: "
        msg += ", ".join(set(action.name for action in failed_constraints))
        super().__init__(msg)


class WorldEntity:
    """ Represents an entity in the world.

    Example of entities commonly found in text-based games:
    rooms, doors, items, etc.
    """

    def __init__(self, var: Variable, name: Optional[str] = None,
                 desc: Optional[str] = None,
                 kb: Optional[KnowledgeBase] = None) -> None:
        """
        Args:
            var: The underlying variable for the entity which is used
                 by TextWorld's inference engine.
            name: The name of the entity that will be displayed in-game.
                  Default: generate one according the variable's type.
            desc: The description of the entity that will be displayed
                  when examining it in the game.
        """
        self.var = var
        self._facts = []
        self.infos = EntityInfo(var.name, var.type)
        self.infos.name = name
        self.infos.desc = desc
        self.content = []
        self.parent = None
        self._kb = kb or KnowledgeBase.default()

    @property
    def id(self) -> str:
        """ Unique name used internally. """
        return self.var.name

    @property
    def type(self) -> str:
        """ Type of this entity. """
        return self.var.type

    @property
    def name(self) -> str:
        """ Name of this entity. """
        return self.infos.name

    @property
    def properties(self) -> List[Proposition]:
        """
        Properties of this object are things that refer to this object and this object alone.
        For instance, 'closed', 'open', and 'locked' are possible properties of 'containers'.
        """
        return [fact for fact in self._facts if len(fact.arguments) == 1]

    @property
    def facts(self) -> List[Proposition]:
        """ All facts related to this entity (or its children content).
        """
        facts = list(self._facts)
        for entity in self.content:
            facts += entity.facts

        return facts

    def add_fact(self, name: str, *entities: List["WorldEntity"]) -> None:
        """ Adds a fact to this entity.

        Args:
            name: The name of the new fact.
            *entities: A list of entities as arguments to the new fact.
        """
        args = [entity.var for entity in entities]
        self._facts.append(Proposition(name, args))

    def remove_fact(self, name: str, *entities: List["WorldEntity"]) -> None:
        args = [entity.var for entity in entities]
        self._facts.remove(Proposition(name, args))

    def add_property(self, name: str) -> None:
        """ Adds a property to this entity.

        A property is a fact that only involves one entity. For instance,
        'closed(c)', 'open(c)', and 'locked(c)' are all properties.

        Args:
            name: The name of the new property.

        """
        self.add_fact(name, self)

    def remove_property(self, name: str) -> None:
        self.remove_fact(name, self)

    def add(self, *entities: List["WorldEntity"]) -> None:
        """ Add children to this entity. """
        if self._kb.types.is_descendant_of(self.type, "r"):
            name = "at"
        elif self._kb.types.is_descendant_of(self.type, ["c", "I"]):
            name = "in"
        elif self._kb.types.is_descendant_of(self.type, "s"):
            name = "on"
        else:
            raise ValueError("Unexpected type {}".format(self.type))

        for entity in entities:
            self.add_fact(name, entity, self)
            self.content.append(entity)
            entity.parent = self

    def remove(self, *entities):
        if self._kb.types.is_descendant_of(self.type, "r"):
            name = "at"
        elif self._kb.types.is_descendant_of(self.type, ["c", "I"]):
            name = "in"
        elif self._kb.types.is_descendant_of(self.type, "s"):
            name = "on"
        else:
            raise ValueError("Unexpected type {}".format(self.type))

        for entity in entities:
            self.remove_fact(name, entity, self)
            self.content.remove(entity)
            entity.parent = None

    def has_property(self, name: str) -> bool:
        """ Determines if this object has a property with the given name.

        Args:
            The name of the property.

        Example:
            >>> from textworld import GameMaker
            >>> M = GameMaker()
            >>> chest = M.new(type="c", name="chest")
            >>> chest.has_property('closed')
            False
            >>> chest.add_property('closed')
            >>> chest.has_property('closed')
            True
        """
        return name in [p.name for p in self.properties]

    def __contains__(self, entity: "WorldEntity") -> bool:
        """ Checks if another entity is a children of this entity.

        Primarily useful for entities that allows children
        (e.g. containers, supporters, rooms, etc).

        Args:
            entity: The entity to check if contained.

        Notes:
            An entity always contains itself.
        """
        if entity == self:
            return True

        for nested_entity in self.content:
            if entity in nested_entity:
                return True

        return False


class WorldRoom(WorldEntity):
    """ Represents a room in the world. """

    __slots__ = list(DIRECTIONS)

    def __init__(self, *args, **kwargs):
        """
        Takes the same arguments as WorldEntity.

        Then, creates a WorldRoomExit for each direction defined in graph_networks.DIRECTIONS, and
        sets exits to be a dict of those names to the newly created rooms. It then sets an attribute
        to each name.

        :param args: The args to pass to WorldEntity
        :param kwargs: The kwargs to pass to WorldEntity
        """
        super().__init__(*args, **kwargs)
        self.exits = {}
        for d in DIRECTIONS:
            exit = WorldRoomExit(self, d)
            self.exits[d] = exit
            setattr(self, d, exit)


class WorldRoomExit:
    """ Represents an exit from a Room.

    These are used to connect `WorldRoom`s to form `WorldPath`s.
    `WorldRoomExit`s are linked to each other through their :py:attr:`dest`.

    When :py:attr:`dest` is `None`, it means there is no path leading to
    this exit yet.
    """

    def __init__(self, src: WorldRoom, direction: str, dest: Optional[WorldRoom] = None) -> None:
        """
        Args:
            src: The WorldRoom that the exit is from.
            direction: The direction the exit is in: north, east, south, and west are common.
            dest: The WorldRoomExit that this exit links to (exits are linked to each other).
        """
        self.direction = direction
        self.src = src    # WorldRoom
        self.dest = dest  # WorldRoomExit


class WorldPath:
    """ Represents a path between two `WorldRoom` objects.

    A `WorldPath` encapsulates the source `WorldRoom`, the source `WorldRoomExit`,
    the destination `WorldRoom` and the destination `WorldRoom`. Optionally, a
    linking door can also be provided.
    """

    def __init__(self, src: WorldRoom, src_exit: WorldRoomExit,
                 dest: WorldRoom, dest_exit: WorldRoomExit,
                 door: Optional[WorldEntity] = None,
                 kb: Optional[KnowledgeBase] = None) -> None:
        """
        Args:
            src: The source room.
            src_exit: The exit of the source room.
            dest: The destination room.
            dest_exit: The exist of the destination room.
            door: The door between the two rooms, if any.
        """
        self.src = src
        self.src_exit = src_exit
        self.dest = dest
        self.dest_exit = dest_exit
        self.door = door
        self._kb = kb or KnowledgeBase.default()
        self.src.exits[self.src_exit].dest = self.dest.exits[self.dest_exit]
        self.dest.exits[self.dest_exit].dest = self.src.exits[self.src_exit]

    @property
    def door(self) -> Optional[WorldEntity]:
        """ The entity representing the door or `None` if there is none."""
        return self._door

    @door.setter
    def door(self, door: WorldEntity) -> None:
        if door is not None and not self._kb.types.is_descendant_of(door.type, "d"):
            msg = "Expecting a WorldEntity of 'door' type."
            raise TypeError(msg)

        self._door = door

    @property
    def facts(self) -> List[Proposition]:
        """ Facts related to this path.

        Returns:
            The facts that make up this path.
        """
        facts = []
        facts.append(Proposition("{}_of".format(self.src_exit), [self.dest.var, self.src.var]))
        facts.append(Proposition("{}_of".format(self.dest_exit), [self.src.var, self.dest.var]))

        if self.door is None or self.door.has_property("open"):
            facts.append(Proposition("free", [self.src.var, self.dest.var]))
            facts.append(Proposition("free", [self.dest.var, self.src.var]))

        if self.door is not None:
            facts.extend(self.door.facts)
            facts.append(Proposition("link", [self.src.var, self.door.var, self.dest.var]))
            facts.append(Proposition("link", [self.dest.var, self.door.var, self.src.var]))

        return facts


class GameMaker:
    """ Stateful utility class for handcrafting text-based games.

    Attributes:
        player (WorldEntity): Entity representing the player.
        inventory (WorldEntity): Entity representing the player's inventory.
        nowhere (List[WorldEntity]): List of out-of-world entities (e.g. objects
                                     that would only appear later in a game).
        rooms (List[WorldRoom]): The rooms present in this world.
        paths (List[WorldPath]): The connections between the rooms.
    """

    def __init__(self, options: Optional[GameOptions] = None) -> None:
        """
        Creates an empty world, with a player and an empty inventory.
        """
        self.options = options or GameOptions()
        self._entities = {}
        self._named_entities = {}
        self.quests = []
        self.rooms = []
        self.paths = []
        self._kb = self.options.kb
        self._types_counts = self._kb.types.count(State(self._kb.logic))
        self.player = self.new(type='P')
        self.inventory = self.new(type='I')
        self.nowhere = []
        self._game = None
        self._distractors_facts = []

    @property
    def state(self) -> State:
        """ Current state of the world. """
        facts = []
        for room in self.rooms:
            facts += room.facts

        for path in self.paths:
            facts += path.facts

        for entity in self.nowhere:
            facts += entity.facts

        facts += self.inventory.facts
        facts += self._distractors_facts

        return State(self._kb.logic, facts)

    @property
    def facts(self) -> Iterable[Proposition]:
        """ All the facts associated to the current game state. """
        return self.state.facts

    def add_fact(self, name: str, *entities: List[WorldEntity]) -> None:
        """ Adds a fact.

        Args:
            name: The name of the new fact.
            *entities: A list of `WorldEntity` as arguments to this fact.
        """
        entities[0].add_fact(name, *entities)

    def new_door(self, path: WorldPath, name: Optional[str] = None,
                 desc: Optional[str] = None) -> WorldEntity:
        """ Creates a new door and add it to the path.

        Args:
            path: A path between two rooms where to add the door.
            name: The name of the door. Default: generate one automatically.
            desc: The description of the door.

        Returns:
            The newly created door.
        """
        path.door = self.new(type='d', name=name, desc=desc)
        return path.door

    def new_room(self, name: Optional[str] = None,
                 desc: Optional[str] = None) -> WorldRoom:
        """ Create new room entity.

        Args:
            name: The name of the room.
            desc: The description of the room.

        Returns:
            The newly created room entity.
        """
        return self.new(type='r', name=name, desc=desc)

    def new(self, type: str, name: Optional[str] = None,
            desc: Optional[str] = None) -> Union[WorldEntity, WorldRoom]:
        """ Creates new entity given its type.

        Args:
            type: The type of the entity.
            name: The name of the entity.
            desc: The description of the entity.

        Returns:
            The newly created entity.

            * If the `type` is `'r'`, then a `WorldRoom` object is returned.
            * Otherwise, a `WorldEntity` is returned.
        """
        var_id = type
        if not self._kb.types.is_constant(type):
            var_id = get_new(type, self._types_counts)

        var = Variable(var_id, type)
        if type == "r":
            entity = WorldRoom(var, name, desc)
            self.rooms.append(entity)
        else:
            entity = WorldEntity(var, name, desc, kb=self._kb)

        self._entities[var_id] = entity
        if entity.name:
            self._named_entities[entity.name] = entity

        return entity

    def move(self, entity: WorldEntity, new_location: WorldEntity) -> None:
        """
        Move an entity to a new location.

        Arguments:
            entity: Entity to move.
            new_location: Where to move the entity.
        """
        entity.parent.remove(entity)
        new_location.add(entity)

    def findall(self, type: str) -> List[WorldEntity]:
        """ Gets all entities of the given type.

        Args:
            type: The type of entity to find.

        Returns:
            All entities which match.
        """
        entities = []
        for entity in self._entities.values():
            if entity.type == type:
                entities.append(entity)

        return entities

    def find_path(self, room1: WorldRoom, room2: WorldRoom) -> Optional[WorldEntity]:
        """ Get the path between two rooms, if it exists.

        Args:
            room1: One of the two rooms.
            room2: The other room.

        Returns:
            The matching path path, if it exists.
        """
        for path in self.paths:
            if (((path.src == room1 and path.dest == room2)
                 or (path.src == room2 and path.dest == room1))):
                return path

        return None

    def find_by_name(self, name: str) -> Optional[WorldEntity]:
        """ Find an entity using its name. """
        return self._named_entities.get(name)

    def set_player(self, room: WorldRoom) -> None:
        """ Place the player in room.

        Args:
            room: The room the player will start in.

        Notes:
            At the moment, the player can only be place once and
            cannot be moved once placed.

        Raises:
            PlayerAlreadySetError: If the player has already been set.
        """
        if self.player in self:
            raise PlayerAlreadySetError()

        room.add(self.player)

    def connect(self, exit1: WorldRoomExit, exit2: WorldRoomExit) -> WorldPath:
        """ Connect two rooms using their exits.

        Args:
            exit1: The exit of the first room to link.
            exit2: The exit of the second room to link.

        Returns:
            The path created by the link between two rooms, with no door.
        """
        if exit1.dest is not None:
            msg = "{}.{} is already linked to {}.{}"
            msg = msg.format(exit1.src, exit1.direction,
                             exit1.dest.src, exit1.dest.direction)
            raise ExitAlreadyUsedError(msg)

        if exit2.dest is not None:
            msg = "{}.{} is already linked to {}.{}"
            msg = msg.format(exit2.src, exit2.direction,
                             exit2.dest.src, exit2.dest.direction)
            raise ExitAlreadyUsedError(msg)

        path = WorldPath(exit1.src, exit1.direction, exit2.src, exit2.direction, kb=self._kb)
        self.paths.append(path)
        return path

    def generate_distractors(self, nb_distractors: int) -> None:
        """ Generates a number of distractors - random objects.

        Args:
            nb_distractors: The number of distractors to game will contain.
        """
        self._distractors_facts = []
        world = World.from_facts(self.facts)
        self._distractors_facts = world.populate(nb_distractors)

    def generate_random_quests(self, nb_quests=1, length: int = 1, breadth: int = 1) -> List[Quest]:
        """ Generates random quests for the game.

        .. warning:: This method overrides any previous quests the game had.

        Args:
            nb_quests: Number of parallel quests, i.e. not sharing a common goal.
            length: Number of actions that need to be performed to complete the game.
            breadth: Number of subquests per independent quest. It controls how nonlinear
                     a quest can be (1: linear).

        Returns:
            The generated quests.
        """
        options = self.options.copy()
        options.nb_parallel_quests = nb_quests
        options.quest_length = length
        options.quest_breadth = breadth
        options.chaining.rng = options.rngs['quest']

        world = World.from_facts(self.facts)
        self.quests = textworld.generator.make_quest(world, options)

        # Calling build will generate the description for the quest.
        self.build()
        return self.quests

    def test(self, walkthrough: bool = False) -> None:
        """ Test the game being built.

        This launches a `textworld.play` session.
        """

        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "test_game.ulx"))

            agent = textworld.agents.HumanAgent(autocompletion=True)
            if walkthrough:
                agent = textworld.agents.WalkthroughAgent()

            textworld.play(game_file, agent=agent)

    def record_quest(self) -> Quest:
        """ Defines the game's quest by recording the commands.

        This launches a `textworld.play` session.

        Returns:
            The resulting quest.
        """
        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "record_quest.ulx"))
            recorder = Recorder()
            agent = textworld.agents.HumanAgent(autocompletion=True)
            textworld.play(game_file, agent=agent, wrappers=[recorder])

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]

        # Assume the last action contains all the relevant facts about the winning condition.
        event = Event(actions=actions)
        self.quests.append(Quest(win_events=[event]))
        # Calling build will generate the description for the quest.
        self.build()
        return self.quests[-1]

    def set_quest_from_commands(self, commands: List[str]) -> Quest:
        """ Defines the game's quest using predefined text commands.

        This launches a `textworld.play` session.

        Args:
            commands: Text commands.

        Returns:
            The resulting quest.
        """
        with make_temp_directory() as tmpdir:
            try:
                game_file = self.compile(pjoin(tmpdir, "record_quest.ulx"))
                recorder = Recorder()
                agent = textworld.agents.WalkthroughAgent(commands)
                textworld.play(game_file, agent=agent, wrappers=[recorder], silent=True)
            except textworld.agents.WalkthroughDone:
                pass  # Quest is done.

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]

        if len(commands) != len(actions):
            unrecognized_commands = [c for c, a in zip(commands, recorder.actions) if a is None]
            raise QuestError("Some of the actions were unrecognized: {}".format(unrecognized_commands))

        event = Event(actions=actions)
        self.quests = [Quest(win_events=[event])]

        # Calling build will generate the description for the quest.
        self.build()
        return self.quests[-1]

    def new_fact(self, name: str, *entities: List["WorldEntity"]) -> None:
        """ Create new fact.

        Args:
            name: The name of the new fact.
            *entities: A list of entities as arguments to the new fact.
        """
        args = [entity.var for entity in entities]
        return Proposition(name, args)

    def new_event_using_commands(self, commands: List[str]) -> Event:
        """ Creates a new event using predefined text commands.

        This launches a `textworld.play` session to execute provided commands.

        Args:
            commands: Text commands.

        Returns:
            The resulting event.
        """
        with make_temp_directory() as tmpdir:
            try:
                game_file = self.compile(pjoin(tmpdir, "record_event.ulx"))
                recorder = Recorder()
                agent = textworld.agents.WalkthroughAgent(commands)
                textworld.play(game_file, agent=agent, wrappers=[recorder], silent=True)
            except textworld.agents.WalkthroughDone:
                pass  # Quest is done.

        # Skip "None" actions.
        actions, commands = zip(*[(a, c) for a, c in zip(recorder.actions, commands) if a is not None])
        event = Event(actions=actions, commands=commands)
        return event

    def new_quest_using_commands(self, commands: List[str]) -> Quest:
        """ Creates a new quest using predefined text commands.

        This launches a `textworld.play` session to execute provided commands.

        Args:
            commands: Text commands.

        Returns:
            The resulting quest.
        """
        event = self.new_event_using_commands(commands)
        return Quest(win_events=[event], commands=event.commands)

    def set_walkthrough(self, commands: List[str]):
        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "set_walkthrough.ulx"))
            env = textworld.start(game_file, infos=EnvInfos(last_action=True, intermediate_reward=True))
            state = env.reset()

            events = {event: event.copy() for quest in self.quests for event in quest.win_events}
            event_progressions = [ep for qp in state._game_progression.quest_progressions for ep in qp.win_events]

            done = False
            actions = []
            for i, cmd in enumerate(commands):
                if done:
                    msg = "Game has ended before finishing playing all commands."
                    raise ValueError(msg)

                events_triggered = [ep.triggered for ep in event_progressions]

                state, score, done = env.step(cmd)
                actions.append(state._last_action)

                for was_triggered, ep in zip(events_triggered, event_progressions):
                    if not was_triggered and ep.triggered:
                        events[ep.event].actions = list(actions)
                        events[ep.event].commands = commands[:i + 1]

        for k, v in events.items():
            k.actions = v.actions
            k.commands = v.commands

    def validate(self) -> bool:
        """ Check if the world is valid and can be compiled.

        A world is valid is the player has been place in a room and
        all constraints (defined in the :ref:`knowledge base <KB>`)
        are respected.
        """
        if self.player not in self:
            msg = "Player position has not been specified. Use 'M.set_player(room)'."
            raise MissingPlayerError(msg)

        failed_constraints = get_failing_constraints(self.state, self._kb)
        if len(failed_constraints) > 0:
            raise FailedConstraintsError(failed_constraints)

        return True

    def build(self, validate: bool = True) -> Game:
        """ Create a `Game` instance given the defined facts.

        Parameters
        ----------
        validate : optional
            If True, check if the game is valid, i.e. respects all constraints.

        Returns
        -------
            Generated game.
        """
        if validate:
            self.validate()  # Validate the state of the world.

        world = World.from_facts(self.facts, kb=self._kb)
        game = Game(world, quests=self.quests)

        # Keep same objectiveif one was provided/generated.
        if self._game and self._game._objective:
            game._objective = self._game._objective

        # Keep names and descriptions that were manually provided.
        used_names = set()
        for k, var_infos in game.infos.items():
            if k in self._entities:
                game.infos[k] = self._entities[k].infos
                used_names.add(game.infos[k].name)

        # Use text grammar to generate name and description.
        options = self.options.grammar.copy()
        options.names_to_exclude += list(used_names)

        grammar = Grammar(options, rng=np.random.RandomState(self.options.seeds["grammar"]))
        game.change_grammar(grammar)
        game.metadata["desc"] = "Generated with textworld.GameMaker."

        self._game = game  # Keep track of previous build.
        return self._game

    def compile(self, path: str) -> str:
        """
        Compile this game.

        Parameters
        ----------
        path :
            Path where to save the generated game.

        Returns
        -------
        game_file
            Path to the game file.
        """
        self._working_game = self.build()
        options = textworld.GameOptions()
        options.path = path
        options.force_recompile = True
        game_file = textworld.generator.compile_game(self._working_game, options)
        return game_file

    def __contains__(self, entity) -> bool:
        """
        Checks if the given entity exists in the world
        :param entity: The entity to check
        :return: True if the entity is in the world; otherwise False
        """
        for room in self.rooms:
            if entity in room:
                return True

        for path in self.paths:
            if entity == path.door:
                return True

        if entity in self.inventory:
            return True

        return False

    def render(self, interactive: bool = False):
        """
        Returns a visual representation of the world.
        :param interactive: opens an interactive session in the browser instead of returning a png.
        :return:
        :param save_screenshot: ONLY FOR WHEN interactive == False. Save screenshot in temp directory.
        :param filename: filename for screenshot
        """
        game = self.build(validate=False)
        return visualize(game, interactive=interactive)

    def import_graph(self, G: nx.Graph) -> List[WorldRoom]:
        """ Convert Graph object to a list of `Proposition`.

        Args:
            G: Graph defining the structure of the world.
        """

        rooms = OrderedDict((n, self.new_room(d.get("name", None))) for n, d in G.nodes.items())

        for src, dest, data in G.edges(data=True):
            src_exit = rooms[src].exits[direction(dest, src)]
            dest_exit = rooms[dest].exits[direction(src, dest)]
            path = self.connect(src_exit, dest_exit)

            if data.get("has_door"):
                door = self.new_door(path, data['door_name'])
                door.add_property(data["door_state"])

        return list(rooms.values())
