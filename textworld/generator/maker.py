# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
from os.path import join as pjoin

from typing import List, Iterable, Union, Optional
try:
    from typing import Collection
except ImportError:
    # Collection is new in Python 3.6 -- fall back on Iterable for 3.5
    from typing import Iterable as Collection

import textworld

from textworld.utils import make_temp_directory

from textworld.generator.data import KnowledgeBase
from textworld.generator import user_query
from textworld.generator.vtypes import get_new
from textworld.logic import State, Variable, Proposition, Action
from textworld.generator.game import Game, World, Quest, Event
from textworld.generator.graph_networks import DIRECTIONS
from textworld.render import visualize
from textworld.envs.wrappers import Recorder


def get_failing_constraints(state):
    fail = Proposition("fail", [])

    failed_constraints = []
    constraints = state.all_applicable_actions(KnowledgeBase.default().constraints.values())
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
                 desc: Optional[str] = None) -> None:
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
        self.name = name
        self.desc = desc
        self.content = []

    @property
    def id(self) -> str:
        """ Unique name used internally. """
        return self.var.name

    @property
    def type(self) -> str:
        """ Type of this entity. """
        return self.var.type

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

    def add_property(self, name: str) -> None:
        """ Adds a property to this entity.

        A property is a fact that only involves one entity. For instance,
        'closed(c)', 'open(c)', and 'locked(c)' are all properties.

        Args:
            name: The name of the new property.

        """
        self.add_fact(name, self)

    def add(self, *entities: List["WorldEntity"]) -> None:
        """ Add children to this entity. """
        if KnowledgeBase.default().types.is_descendant_of(self.type, "r"):
            name = "at"
        elif KnowledgeBase.default().types.is_descendant_of(self.type, ["c", "I"]):
            name = "in"
        elif KnowledgeBase.default().types.is_descendant_of(self.type, "s"):
            name = "on"
        else:
            raise ValueError("Unexpected type {}".format(self.type))

        for entity in entities:
            self.add_fact(name, entity, self)
            self.content.append(entity)

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
        for direction in DIRECTIONS:
            exit = WorldRoomExit(self, direction)
            self.exits[direction] = exit
            setattr(self, direction, exit)


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
                 door: Optional[WorldEntity] = None) -> None:
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
        self.src.exits[self.src_exit].dest = self.dest.exits[self.dest_exit]
        self.dest.exits[self.dest_exit].dest = self.src.exits[self.src_exit]

    @property
    def door(self) -> Optional[WorldEntity]:
        """ The entity representing the door or `None` if there is none."""
        return self._door

    @door.setter
    def door(self, door: WorldEntity) -> None:
        if door is not None and not KnowledgeBase.default().types.is_descendant_of(door.type, "d"):
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
        inventory (WorldEntity): Player's envi entity.
        rooms (List[WorldRoom]): The rooms present in this world.
    """

    def __init__(self) -> None:
        """
        Creates an empty world, with a player and an empty inventory.
        """
        self._entities = {}
        self.quests = []
        self.rooms = []
        self.paths = []
        self._types_counts = KnowledgeBase.default().types.count(State())
        self.player = self.new(type='P')
        self.inventory = self.new(type='I')
        self.grammar = textworld.generator.make_grammar()
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

        facts += self.inventory.facts
        facts += self._distractors_facts

        return State(facts)

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
        if not KnowledgeBase.default().types.is_constant(type):
            var_id = get_new(type, self._types_counts)

        var = Variable(var_id, type)
        if type == "r":
            entity = WorldRoom(var, name, desc)
            self.rooms.append(entity)
        else:
            entity = WorldEntity(var, name, desc)

        self._entities[var_id] = entity
        return entity

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

        path = WorldPath(exit1.src, exit1.direction, exit2.src, exit2.direction)
        self.paths.append(path)
        return path

    def add_distractors(self, nb_distractors: int) -> None:
        """ Adds a number of distractors - random objects.

        Args:
            nb_distractors: The number of distractors to add.
        """
        self._distractors_facts = []
        world = World.from_facts(self.facts)
        self._distractors_facts = world.populate(nb_distractors)

    def add_random_quest(self, max_length: int) -> Quest:
        """ Generates a random quest for the game.

        Calling this method replaced all previous quests.

        Args:
            max_length: The maximum length of the quest to generate.

        Returns:
            The generated quest.
        """
        world = World.from_facts(self.facts)
        self.quests.append(textworld.generator.make_quest(world, max_length))

        # Calling build will generate the description for the quest.
        self.build()
        return self.quests[-1]

    def test(self) -> None:
        """ Test the game being built.

        This launches a `textworld.play` session.
        """
        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "test_game.ulx"))
            textworld.play(game_file)

    def record_quest(self, ask_for_state: bool = False) -> Quest:
        """ Defines the game's quest by recording the commands.

        This launches a `textworld.play` session.

        Args:
            ask_for_state: If true, the user will be asked to specify
                           which set of facts of the final state are
                           should be true in order to consider the quest
                           as completed.

        Returns:
            The resulting quest.
        """
        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "record_quest.ulx"))
            recorder = Recorder()
            textworld.play(game_file, wrapper=recorder)

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]

        # Ask the user which quests have important state, if this is set
        # (if not, we assume the last action contains all the relevant facts)
        winning_facts = None
        if ask_for_state and recorder.last_game_state is not None:
            winning_facts = [user_query.query_for_important_facts(actions=recorder.actions,
                                                                  facts=recorder.last_game_state.state.facts,
                                                                  varinfos=self._working_game.infos)]

        event = Event(actions=actions, conditions=winning_facts)
        self.quests.append(Quest(win_events=[event]))
        # Calling build will generate the description for the quest.
        self.build()
        return self.quests[-1]

    def set_quest_from_commands(self, commands: List[str], ask_for_state: bool = False) -> Quest:
        """ Defines the game's quest using predefined text commands.

        This launches a `textworld.play` session.

        Args:
            commands: Text commands.
            ask_for_state: If true, the user will be asked to specify
                           which set of facts of the final state are
                           should be true in order to consider the quest
                           as completed.

        Returns:
            The resulting quest.
        """
        with make_temp_directory() as tmpdir:
            try:
                game_file = self.compile(pjoin(tmpdir, "record_quest.ulx"))
                recorder = Recorder()
                agent = textworld.agents.WalkthroughAgent(commands)
                textworld.play(game_file, agent=agent, wrapper=recorder, silent=True)
            except textworld.agents.WalkthroughDone:
                pass  # Quest is done.

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]

        # Ask the user which quests have important state, if this is set
        # (if not, we assume the last action contains all the relevant facts)
        winning_facts = None
        if ask_for_state and recorder.last_game_state is not None:
            winning_facts = [user_query.query_for_important_facts(actions=recorder.actions,
                                                                  facts=recorder.last_game_state.state.facts,
                                                                  varinfos=self._working_game.infos)]

        event = Event(actions=actions, conditions=winning_facts)
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
                textworld.play(game_file, agent=agent, wrapper=recorder, silent=True)
            except textworld.agents.WalkthroughDone:
                pass  # Quest is done.

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]
        event = Event(actions=actions)
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
        return Quest(win_events=[event])

    def validate(self) -> bool:
        """ Check if the world is valid and can be compiled.

        A world is valid is the player has been place in a room and
        all constraints (defined in the :ref:`knowledge base <KB>`)
        are respected.
        """
        if self.player not in self:
            msg = "Player position has not been specified. Use 'M.set_player(room)'."
            raise MissingPlayerError(msg)

        failed_constraints = get_failing_constraints(self.state)
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

        world = World.from_facts(self.facts)
        game = Game(world, quests=self.quests)

        # Keep names and descriptions that were manually provided.
        for k, var_infos in game.infos.items():
            if k in self._entities:
                var_infos.name = self._entities[k].name
                var_infos.desc = self._entities[k].desc

            # If we can, reuse information generated during last build.
            if self._game is not None and k in self._game.infos:
                # var_infos.desc = self._game.infos[k].desc
                var_infos.name = self._game.infos[k].name
                var_infos.adj = self._game.infos[k].adj
                var_infos.noun = self._game.infos[k].noun
                var_infos.room_type = self._game.infos[k].room_type

        # Generate text for recently added objects.
        game.change_grammar(self.grammar)
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
        game.change_grammar(self.grammar)  # Generate missing object names.
        return visualize(game, interactive=interactive)
