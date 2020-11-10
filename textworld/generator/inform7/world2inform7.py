# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re
import os
import shutil
import warnings
import subprocess
import textwrap
from os.path import join as pjoin
from typing import Iterable, Optional, List

from pkg_resources import Requirement, resource_filename

from textworld.utils import make_temp_directory, str2bool, chunk

from textworld.generator.game import Game
from textworld.generator.world import WorldRoom, WorldEntity
from textworld.logic import Signature, Proposition, Action, Variable


I7_DEFAULT_PATH = resource_filename(Requirement.parse('textworld'), 'textworld/thirdparty/inform7-6M62')


class TextworldInform7Warning(UserWarning):
    pass


class CouldNotCompileGameError(RuntimeError):
    pass


def split_string(string, name, cutoff=200):
    source = ""

    parts = []
    splits = re.split(r"\[line break\]", string)  # Avoid splitting [line break].
    for i, split in enumerate(splits):
        chunks = ["".join(c) for c in chunk(split, cutoff)]
        for j, part in enumerate(chunks):
            if i < len(splits) - 1 and j == len(chunks) - 1:
                part += "[line break]"

            part_name = "{} part {}".format(name, len(parts))
            text = "The {name} is some text that varies. The {name} is \"{desc}\".\n"
            source += text.format(name=part_name, desc=part)
            parts.append(part_name)

    new_string = "".join("[{}]".format(part) for part in parts)
    return source, new_string


class Inform7Game:
    VERSION = 1

    def __init__(self, game: Game) -> None:
        self.game = game
        self.entity_infos = self.game.infos
        self.kb = self.game.kb
        self.use_i7_description = False  # XXX: should it be removed?

    def gen_source_for_map(self, src_room: WorldRoom) -> str:
        source = ""
        src_room_id = src_room.id

        for src_exit, dest_room in src_room.exits.items():
            dest_room_id = dest_room.id

            if src_exit in src_room.doors:
                door = src_room.doors[src_exit]
                dest_exit = [k for k, v in dest_room.doors.items() if v == door][0]
                template = "{src_exit} of {src} and {dest_exit} of {dest} is a door called {door}.\n"
                source += template.format(src_exit=src_exit,
                                          src=src_room_id,
                                          dest_exit=dest_exit,
                                          dest=dest_room_id,
                                          door=door.name)
            else:
                sig = Signature("{}_of".format(src_exit), ["r", "r"])
                _, template = self.kb.inform7_predicates[sig]
                mapping = {'r': dest_room_id, "r'": src_room_id}
                source += template.format(**mapping) + ".\n"

        return source

    def gen_source_for_attribute(self, attr: Proposition) -> Optional[str]:
        pt = self.kb.inform7_predicates.get(attr.signature)
        if pt is None:
            msg = "Undefined Inform7's predicate: {}".format(attr.signature)
            warnings.warn(msg, TextworldInform7Warning)
            return None

        pred, template = pt
        mapping = pred.match(attr)
        mapping = {ph.name: var.name for ph, var in mapping.items()}
        return template.format(**mapping)

    def gen_source_for_attributes(self, attributes: Iterable[Proposition]) -> str:
        source = ""
        for attr in attributes:
            source_attr = self.gen_source_for_attribute(attr)
            if source_attr:
                source += source_attr + ".\n"

        return source

    def gen_source_for_conditions(self, conds: Iterable[Proposition]) -> str:
        """Generate Inform 7 source for winning/losing conditions."""

        i7_conds = []
        for cond in conds:
            i7_cond = self.gen_source_for_attribute(cond)
            if i7_cond:
                i7_conds.append(i7_cond)

        # HACK: In Inform7 we have to mention a container/door is unlocked AND closed.
        for cond in conds:
            if cond.name == "closed":
                i7_conds.append("the {} is unlocked".format(cond.arguments[0].name))

        return " and ".join(i7_conds)

    def gen_source_for_objects(self, objects: Iterable[WorldEntity]) -> str:
        source = ""
        for obj in objects:
            if obj.type in ["P", "I"]:
                continue  # Skip player

            obj_infos = self.entity_infos[obj.id]
            if not self.use_i7_description:
                # Describe the object.
                source += 'The description of {} is "{}".\n'.format(obj_infos.id, obj_infos.desc.replace("\n", "[line break]"))
                source += 'The printed name of {} is "{}".\n'.format(obj_infos.id, obj_infos.name)

                if obj_infos.indefinite:
                    source += 'The indefinite article of {} is "{}".\n'.format(obj_infos.id, obj_infos.indefinite)

                if obj_infos.definite:
                    source += 'The definite article of {} is "{}".\n'.format(obj_infos.id, obj_infos.definite)

                if obj_infos.synonyms:
                    for synonym in obj_infos.synonyms:
                        source += 'Understand "{}" as {}.\n'.format(synonym, obj_infos.id)

                # Since we use objects' id in Inform7 source code, we need to specify how to refer to them.
                if obj_infos.name:
                    source += 'Understand "{}" as {}.\n'.format(obj_infos.name, obj_infos.id)

                    # If an object's name is composed of multiple words, make them all refer to the object.
                    words = obj_infos.name.split()
                    if len(words) > 1:
                        for word in words:
                            if word.lower() not in ["the", "of"]:
                                source += 'Understand "{}" as {}.\n'.format(word, obj_infos.id)

            # List object's attributes
            source += self.gen_source_for_attributes(obj.get_attributes())

        return source

    def gen_source_for_rooms(self) -> str:
        source = ""
        for room in self.game.world.rooms:
            room_infos = self.entity_infos[room.id]
            room_name = room_infos.name

            if not self.use_i7_description:
                # Describe the room.
                room_desc = room_infos.desc
                source += "Understand \"{}\" as {}.\n".format(room_name, room.id)
                source += "The internal name of {} is \"{}\".\n".format(room.id, room_name)
                source += "The printed name of {} is \"-= {} =-\".\n".format(room.id, str.title(room_name))

                parts = []
                splits = re.split(r"\[end if\]", room_desc)
                for split in splits:
                    part_name = "{} part {}".format(room_name, len(parts))
                    text = "The {name} is some text that varies. The {name} is \"{desc}\".\n"
                    if split != splits[-1]:
                        split += "[end if]"

                    source += text.format(name=part_name, desc=split)
                    parts.append(part_name)

                source += "The description of {} is \"{}\".\n".format(room.id, "".join("[{}]".format(part) for part in parts))
                source += "\n"

            # List the room's attributes.
            source += self.gen_source_for_map(room)

        return source

    def _get_name_mapping(self, action):
        mapping = self.kb.rules[action.name].match(action)
        return {ph.name: self.entity_infos[var.name].name for ph, var in mapping.items()}

    def gen_commands_from_actions(self, actions: Iterable[Action]) -> List[str]:
        commands = []
        for action in actions:
            command = "None"
            if action is not None:
                if getattr(action, "command_template"):
                    mapping = {var.name: self.entity_infos[var.name].name for var in action.variables}
                    command = action.format_command(mapping)
                else:
                    msg = ("Using slower text commands from action generation."
                           " Regenerate your games, to get a faster version.")
                    warnings.warn(msg, TextworldInform7Warning)
                    command = self.kb.inform7_commands[action.name]
                    command = command.format(**self._get_name_mapping(action))

            commands.append(command)

        return commands

    def get_human_readable_fact(self, fact: Proposition) -> Proposition:
        def _get_name(info):
            return info.name if info.name else info.id

        arguments = [Variable(_get_name(self.entity_infos[var.name]), var.type) for var in fact.arguments]
        return Proposition(fact.name, arguments)

    def get_human_readable_action(self, action: Action) -> Action:
        precondition = list(map(self.get_human_readable_fact, action.preconditions))
        postconditions = list(map(self.get_human_readable_fact, action.postconditions))
        name = self.kb.inform7_commands[action.name].split("{")[0].strip()
        return Action(name, precondition, postconditions)

    def detect_action(self, i7_event: str, actions: Iterable[Action]) -> Optional[Action]:
        """ Detect which action corresponds to a Inform7 event.

        Arguments:
            i7_event: Inform7 event detected.
            actions: List of action to match the Inform7 event against.

        Returns:
            Action corresponding to the provided Inform7 event.
        """
        # Prioritze actions with many precondition terms.
        actions = sorted(actions, key=lambda a: len(a.preconditions), reverse=True)
        for action in actions:
            event = self.kb.inform7_events[action.name]
            if event.format(**self._get_name_mapping(action)).lower() == i7_event.lower():
                return action

        return None

    def define_inform7_kinds(self) -> str:
        """ Generate Inform 7 kind definitions. """
        type_defs = ""
        type_desc = ""

        # Making sure we loop through the types hierarchy from the root to the leaves.
        roots = [type for type in self.kb.logic.types if len(type.parents) == 0]
        for root in roots:
            for type_ in root.subtypes:
                if type_.name not in self.kb.inform7_variables:
                    continue

                kind = self.kb.inform7_variables[type_.name]
                for parent in type_.parents:
                    parent_kind = self.kb.inform7_variables[parent]
                    msg = '{} is a kind of {}.\n'.format(kind, parent_kind)
                    type_defs += msg

                desc = self.kb.inform7_variables_description[type_.name]
                if desc:
                    type_desc += desc + '\n'

        return type_defs + type_desc

    def gen_source(self, seed: int = 1234) -> str:
        source = ""
        source += "Use MAX_STATIC_DATA of 500000.\n"  # To generate game with 300+ locations.
        source += "When play begins, seed the random-number generator with {}.\n\n".format(seed)
        source += self.define_inform7_kinds()
        # Mention that rooms have a special text attribute called 'internal name'.
        source += "A room has a text called internal name.\n\n"

        # Define custom addons.
        source += self.kb.inform7_addons_code + "\n"

        # Declare all rooms.
        room_names = [room.id for room in self.game.world.rooms]
        source += "The " + " and the ".join(room_names) + " are rooms.\n\n"

        source += self.gen_source_for_rooms() + "\n"

        # Declare all objects
        for vtype in self.game.kb.types:
            if vtype in ["P", "I"]:
                continue  # Skip player and inventory.

            entities = self.game.world.get_entities_per_type(vtype)
            if len(entities) == 0:
                continue  # No entity of that specific type.

            kind = self.kb.inform7_variables[vtype]
            names = [entity.id for entity in entities]
            source += "The " + " and the ".join(names) + " are {}s.\n".format(kind)
            # All objects are privately-named and we manually define all "Understand as" phrases needed.
            source += "The " + " and the ".join(names) + " are privately-named.\n"

        # Process the objects.
        source += "\n"
        source += self.gen_source_for_objects(self.game.world.objects)
        source += "\n\n"

        # Place the player.
        source += "The player is in {}.\n\n".format(self.entity_infos[self.game.world.player_room.id].id)

        objective = self.game.objective.replace("\n", "[line break]")
        maximum_score = 0
        for quest_id, quest in enumerate(self.game.quests):
            maximum_score += quest.reward

            quest_completed = textwrap.dedent("""\
            The quest{quest_id} completed is a truth state that varies.
            The quest{quest_id} completed is usually false.
            """)
            source += quest_completed.format(quest_id=quest_id)

            for event_id, event in enumerate(quest.win_events):
                commands = self.gen_commands_from_actions(event.actions)
                event.commands = commands

                walkthrough = '\nTest quest{}_{} with "{}"\n\n'.format(quest_id, event_id, " / ".join(commands))
                source += walkthrough

            # Add winning and losing conditions for quest.
            quest_ending_conditions = textwrap.dedent("""\
            if quest{quest_id} completed is true:
                do nothing;""".format(quest_id=quest_id))

            fail_template = textwrap.dedent("""
            else if {conditions}:
                end the story; [Lost]""")

            win_template = textwrap.dedent("""
            else if {conditions}:
                increase the score by {reward}; [Quest completed]
                Now the quest{quest_id} completed is true;""")

            for fail_event in quest.fail_events:
                conditions = self.gen_source_for_conditions(fail_event.condition.preconditions)
                quest_ending_conditions += fail_template.format(conditions=conditions)

            for win_event in quest.win_events:
                conditions = self.gen_source_for_conditions(win_event.condition.preconditions)
                quest_ending_conditions += win_template.format(conditions=conditions,
                                                               reward=quest.reward,
                                                               quest_id=quest_id)

            quest_ending = """\
            Every turn:\n{conditions}

            """.format(conditions=textwrap.indent(quest_ending_conditions, "                "))
            source += textwrap.dedent(quest_ending)

        # Enable scoring is at least one quest has nonzero reward.
        if maximum_score != 0:
            source += "Use scoring. The maximum score is {}.\n".format(maximum_score)

        # Build test condition for winning the game.
        game_winning_test = "1 is 0 [always false]"
        if len(self.game.quests) > 0:
            game_winning_test = "score is maximum score"

        # Remove square bracket when printing score increases. Square brackets are conflicting with
        # Inform7's events parser in tw_inform7.py.
        # And add winning conditions for the game.
        source += textwrap.dedent("""\
        This is the simpler notify score changes rule:
            If the score is not the last notified score:
                let V be the score - the last notified score;
                say "Your score has just gone up by [V in words] ";
                if V > 1:
                    say "points.";
                else:
                    say "point.";
                Now the last notified score is the score;
            if {game_winning_test}:
                end the story finally; [Win]

        The simpler notify score changes rule substitutes for the notify score changes rule.

        """.format(game_winning_test=game_winning_test))

        if not self.use_i7_description:
            # Remove Inform7 listing of nondescript items.
            source += textwrap.dedent("""\
            Rule for listing nondescript items:
                stop.

            """)

        else:
            # List exits in room description
            source += textwrap.dedent("""\
            [Ref: http://dhayton.haverford.edu/wp-content/uploads/Inform-manuals/Rex434.html#e434]
            The initial appearance of a door is usually "Nearby [an item described] leads [if the other side of the item described is visited][direction of the item described from the location] to [the other side][otherwise][direction of the item described from the location][end if]. It is [if open]open[else if closed]closed[otherwise]closed[end if]."

            Direction-relevance relates a door (called X) to a direction (called Y) when the direction of X from the location is Y. The verb to be directionally-relevant to means the direction-relevance relation.

            Understand "[something related by direction-relevance] door" as a door.

            Rule for printing a parser error when the player's command includes "[non-door direction] door":
                say "There is no door in that direction." instead.

            Definition: a direction (called direction D) is non-door:
                let the target be the room-or-door direction D from the location;
                if the target is a door:
                    no;
                yes;

            """)  # noqa: E501

            source += textwrap.dedent("""\
            Definition: a direction (called thataway) is viable if the room thataway from the location is a room and the room-or-door thataway from the location is a room.

            After looking:
                if list of viable directions is not empty:
                    say "You can also go [list of viable directions] from here.".

            """)  # noqa: E501

        # Replace default banner with a greeting message and the quest description.
        source += textwrap.dedent("""\
        Rule for printing the banner text:
            say "[fixed letter spacing]";
            say "                    ________  ________  __    __  ________        [line break]";
            say "                   |        \|        \|  \  |  \|        \       [line break]";
            say "                    \$$$$$$$$| $$$$$$$$| $$  | $$ \$$$$$$$$       [line break]";
            say "                      | $$   | $$__     \$$\/  $$   | $$          [line break]";
            say "                      | $$   | $$  \     >$$  $$    | $$          [line break]";
            say "                      | $$   | $$$$$    /  $$$$\    | $$          [line break]";
            say "                      | $$   | $$_____ |  $$ \$$\   | $$          [line break]";
            say "                      | $$   | $$     \| $$  | $$   | $$          [line break]";
            say "                       \$$    \$$$$$$$$ \$$   \$$    \$$          [line break]";
            say "              __       __   ______   _______   __        _______  [line break]";
            say "             |  \  _  |  \ /      \ |       \ |  \      |       \ [line break]";
            say "             | $$ / \ | $$|  $$$$$$\| $$$$$$$\| $$      | $$$$$$$\[line break]";
            say "             | $$/  $\| $$| $$  | $$| $$__| $$| $$      | $$  | $$[line break]";
            say "             | $$  $$$\ $$| $$  | $$| $$    $$| $$      | $$  | $$[line break]";
            say "             | $$ $$\$$\$$| $$  | $$| $$$$$$$\| $$      | $$  | $$[line break]";
            say "             | $$$$  \$$$$| $$__/ $$| $$  | $$| $$_____ | $$__/ $$[line break]";
            say "             | $$$    \$$$ \$$    $$| $$  | $$| $$     \| $$    $$[line break]";
            say "              \$$      \$$  \$$$$$$  \$$   \$$ \$$$$$$$$ \$$$$$$$ [line break]";
            say "[variable letter spacing][line break]";
            say "[objective][line break]".

        """)  # noqa: W605

        # Simply display *** The End *** when game ends.
        source += textwrap.dedent("""\
        Include Basic Screen Effects by Emily Short.

        Rule for printing the player's obituary:
            if story has ended finally:
                center "*** The End ***";
            else:
                center "*** You lost! ***";
            say paragraph break;
            say "You scored [score] out of a possible [maximum score], in [turn count] turn(s).";
            [wait for any key;
            stop game abruptly;]
            rule succeeds.

        """)

        # Disable implicitly taking something.
        source += textwrap.dedent("""\
        Rule for implicitly taking something (called target):
            if target is fixed in place:
                say "The [target] is fixed in place.";
            otherwise:
                say "You need to take the [target] first.";
                set pronouns from target;
            stop.

        """)

        # Referring to an object by its whole name shouldn't be ambiguous.
        source += textwrap.dedent("""\
        Does the player mean doing something:
            if the noun is not nothing and the second noun is nothing and the player's command matches the text printed name of the noun:
                it is likely;
            if the noun is nothing and the second noun is not nothing and the player's command matches the text printed name of the second noun:
                it is likely;
            if the noun is not nothing and the second noun is not nothing and the player's command matches the text printed name of the noun and the player's command matches the text printed name of the second noun:
                it is very likely.  [Handle action with two arguments.]

        """)  # noqa: E501

        # Useful for listing room contents with their properties.
        source += textwrap.dedent("""\
        Printing the content of the room is an activity.
        Rule for printing the content of the room:
            let R be the location of the player;
            say "Room contents:[line break]";
            list the contents of R, with newlines, indented, including all contents, with extra indentation.

        """)

        # Useful for listing world contents with their properties.
        source += textwrap.dedent("""\
        Printing the content of the world is an activity.
        Rule for printing the content of the world:
            let L be the list of the rooms;
            say "World: [line break]";
            repeat with R running through L:
                say "  [the internal name of R][line break]";
            repeat with R running through L:
                say "[the internal name of R]:[line break]";
                if the list of things in R is empty:
                    say "  nothing[line break]";
                otherwise:
                    list the contents of R, with newlines, indented, including all contents, with extra indentation.

        """)

        # Useful for listing inventory contents with their properties.
        source += textwrap.dedent("""\
        Printing the content of the inventory is an activity.
        Rule for printing the content of the inventory:
            say "You are carrying: ";
            list the contents of the player, as a sentence, giving inventory information, including all contents;
            say ".".

        """)  # noqa: E501

        # Useful for listing inventory contents with their properties.
        source += textwrap.dedent("""\
        The print standard inventory rule is not listed in any rulebook.
        Carry out taking inventory (this is the new print inventory rule):
            say "You are carrying: ";
            list the contents of the player, as a sentence, giving inventory information, including all contents;
            say ".".

        """)  # noqa: E501

        # Useful for listing off-stage contents with their properties.
        source += textwrap.dedent("""\
        Printing the content of nowhere is an activity.
        Rule for printing the content of nowhere:
            say "Nowhere:[line break]";
            let L be the list of the off-stage things;
            repeat with thing running through L:
                say "  [thing][line break]";

        """)

        # Useful for listing things laying on the floor.
        source += textwrap.dedent("""\
        Printing the things on the floor is an activity.
        Rule for printing the things on the floor:
            let R be the location of the player;
            let L be the list of things in R;
            remove yourself from L;
            remove the list of containers from L;
            remove the list of supporters from L;
            remove the list of doors from L;
            if the number of entries in L is greater than 0:
                say "There is [L with indefinite articles] on the floor.";

        """)

        # Print properties of objects when listing the inventory contents and the room contents.
        source += textwrap.dedent("""\
        After printing the name of something (called target) while
        printing the content of the room
        or printing the content of the world
        or printing the content of the inventory
        or printing the content of nowhere:
            follow the property-aggregation rules for the target.

        The property-aggregation rules are an object-based rulebook.
        The property-aggregation rulebook has a list of text called the tagline.

        [At the moment, we only support "open/unlocked", "closed/unlocked" and "closed/locked" for doors and containers.]
        [A first property-aggregation rule for an openable open thing (this is the mention open openables rule):
            add "open" to the tagline.

        A property-aggregation rule for an openable closed thing (this is the mention closed openables rule):
            add "closed" to the tagline.

        A property-aggregation rule for an lockable unlocked thing (this is the mention unlocked lockable rule):
            add "unlocked" to the tagline.

        A property-aggregation rule for an lockable locked thing (this is the mention locked lockable rule):
            add "locked" to the tagline.]

        A first property-aggregation rule for an openable lockable open unlocked thing (this is the mention open openables rule):
            add "open" to the tagline.

        A property-aggregation rule for an openable lockable closed unlocked thing (this is the mention closed openables rule):
            add "closed" to the tagline.

        A property-aggregation rule for an openable lockable closed locked thing (this is the mention locked openables rule):
            add "locked" to the tagline.

        A property-aggregation rule for a lockable thing (called the lockable thing) (this is the mention matching key of lockable rule):
            let X be the matching key of the lockable thing;
            if X is not nothing:
                add "match [X]" to the tagline.

        A property-aggregation rule for an edible off-stage thing (this is the mention eaten edible rule):
            add "eaten" to the tagline.

        The last property-aggregation rule (this is the print aggregated properties rule):
            if the number of entries in the tagline is greater than 0:
                say " ([tagline])";
                rule succeeds;
            rule fails;

        """)  # noqa: E501

        objective_parts, objective_text = split_string(objective, "objective")
        objective_parts = textwrap.indent(objective_parts, "        ")
        source += textwrap.dedent("""\
        {objective_parts}
        An objective is some text that varies. The objective is "{objective}".
        """.format(objective_parts=objective_parts.lstrip(), objective=objective_text))

        # Special command to print the objective of the game, if any.
        source += textwrap.dedent("""\
        Printing the objective is an action applying to nothing.
        Carry out printing the objective:
            say "[objective]".

        Understand "goal" as printing the objective.

        """)

        # Customize reporting of the "take" action.
        # Ref: http://inform7.com/learn/man/RB_6_8.html
        source += textwrap.dedent("""\
        The taking action has an object called previous locale (matched as "from").

        Setting action variables for taking:
            now previous locale is the holder of the noun.

        Report taking something from the location:
            say "You pick up [the noun] from the ground." instead.

        Report taking something:
            say "You take [the noun] from [the previous locale]." instead.

        Report dropping something:
            say "You drop [the noun] on the ground." instead.

        """)

        # Special command to print game state.
        source += textwrap.dedent("""\
        The print state option is a truth state that varies.
        The print state option is usually false.

        Turning on the print state option is an action applying to nothing.
        Carry out turning on the print state option:
            Now the print state option is true.

        Turning off the print state option is an action applying to nothing.
        Carry out turning off the print state option:
            Now the print state option is false.

        Printing the state is an activity.
        Rule for printing the state:
            let R be the location of the player;
            say "Room: [line break] [the internal name of R][line break]";
            [say "[line break]";
            carry out the printing the content of the room activity;]
            say "[line break]";
            carry out the printing the content of the world activity;
            say "[line break]";
            carry out the printing the content of the inventory activity;
            say "[line break]";
            carry out the printing the content of nowhere activity;
            say "[line break]".

        Printing the entire state is an action applying to nothing.
        Carry out printing the entire state:
            say "-=STATE START=-[line break]";
            carry out the printing the state activity;
            say "[line break]Score:[line break] [score]/[maximum score][line break]";
            say "[line break]Objective:[line break] [objective][line break]";
            say "[line break]Inventory description:[line break]";
            say "  You are carrying: [a list of things carried by the player].[line break]";
            say "[line break]Room description:[line break]";
            try looking;
            say "[line break]-=STATE STOP=-";

        Every turn:
            if extra description command option is true:
                say "<description>";
                try looking;
                say "</description>";
            if extra inventory command option is true:
                say "<inventory>";
                try taking inventory;
                say "</inventory>";
            if extra score command option is true:
                say "<score>[line break][score][line break]</score>";
            if extra score command option is true:
                say "<moves>[line break][turn count][line break]</moves>";
            if print state option is true:
                try printing the entire state;

        When play ends:
            if print state option is true:
                try printing the entire state;

        After looking:
            carry out the printing the things on the floor activity.

        Understand "print_state" as printing the entire state.
        Understand "enable print state option" as turning on the print state option.
        Understand "disable print state option" as turning off the print state option.

        """)

        # Disable implicitly opening/unlocking door.
        source += textwrap.dedent("""\
        Before going through a closed door (called the blocking door):
            say "You have to open the [blocking door] first.";
            stop.

        Before opening a locked door (called the locked door):
            let X be the matching key of the locked door;
            if X is nothing:
                say "The [locked door] is welded shut.";
            otherwise:
                say "You have to unlock the [locked door] with the [X] first.";
            stop.

        Before opening a locked container (called the locked container):
            let X be the matching key of the locked container;
            if X is nothing:
                say "The [locked container] is welded shut.";
            otherwise:
                say "You have to unlock the [locked container] with the [X] first.";
            stop.

        """)

        # Add new actions.
        source += textwrap.dedent("""\
        Displaying help message is an action applying to nothing.
        Carry out displaying help message:
            say "[fixed letter spacing]Available commands:[line break]";
            say "  look:                describe the current room[line break]";
            say "  goal:                print the goal of this game[line break]";
            say "  inventory:           print player's inventory[line break]";
            say "  go <dir>:            move the player north, east, south or west[line break]";
            say "  examine ...:         examine something more closely[line break]";
            say "  eat ...:             eat edible food[line break]";
            say "  open ...:            open a door or a container[line break]";
            say "  close ...:           close a door or a container[line break]";
            say "  drop ...:            drop an object on the floor[line break]";
            say "  take ...:            take an object that is on the floor[line break]";
            say "  put ... on ...:      place an object on a supporter[line break]";
            say "  take ... from ...:   take an object from a container or a supporter[line break]";
            say "  insert ... into ...: place an object into a container[line break]";
            say "  lock ... with ...:   lock a door or a container with a key[line break]";
            say "  unlock ... with ...: unlock a door or a container with a key[line break]";

        Understand "help" as displaying help message.

        """)

        # Disable take/get all.
        source += textwrap.dedent("""\
            Taking all is an action applying to nothing.
            Check taking all:
                say "You have to be more specific!";
                rule fails.

            Understand "take all" as taking all.
            Understand "get all" as taking all.
            Understand "pick up all" as taking all.

            Understand "take each" as taking all.
            Understand "get each" as taking all.
            Understand "pick up each" as taking all.

            Understand "take everything" as taking all.
            Understand "get everything" as taking all.
            Understand "pick up everything" as taking all.

        """)

        # Special command to issue "look" command at every step.
        source += textwrap.dedent("""\
        The extra description command option is a truth state that varies.
        The extra description command option is usually false.

        Turning on the extra description command option is an action applying to nothing.
        Carry out turning on the extra description command option:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            Now the extra description command option is true.

        Understand "tw-extra-infos description" as turning on the extra description command option.

        """)

        # Special command to issue "inventory" command at every step.
        source += textwrap.dedent("""\
        The extra inventory command option is a truth state that varies.
        The extra inventory command option is usually false.

        Turning on the extra inventory command option is an action applying to nothing.
        Carry out turning on the extra inventory command option:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            Now the extra inventory command option is true.

        Understand "tw-extra-infos inventory" as turning on the extra inventory command option.

        """)

        # Special command to issue "score" command at every step.
        source += textwrap.dedent("""\
        The extra score command option is a truth state that varies.
        The extra score command option is usually false.

        Turning on the extra score command option is an action applying to nothing.
        Carry out turning on the extra score command option:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            Now the extra score command option is true.

        Understand "tw-extra-infos score" as turning on the extra score command option.

        """)

        # Special command to get number of "moves" at every step.
        source += textwrap.dedent("""\
        The extra moves command option is a truth state that varies.
        The extra moves command option is usually false.

        Turning on the extra moves command option is an action applying to nothing.
        Carry out turning on the extra moves command option:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            Now the extra moves command option is true.

        Understand "tw-extra-infos moves" as turning on the extra moves command option.

        """)

        # Tracing actions.
        source += textwrap.dedent("""\
            To trace the actions:
                (- trace_actions = 1; -).

            Tracing the actions is an action applying to nothing.
            Carry out tracing the actions:
                Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
                trace the actions;

            Understand "tw-trace-actions" as tracing the actions.

        """)

        # Special command to restrict possible actions.
        source += textwrap.dedent("""\
        The restrict commands option is a truth state that varies.
        The restrict commands option is usually false.

        Turning on the restrict commands option is an action applying to nothing.
        Carry out turning on the restrict commands option:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            Now the restrict commands option is true.

        Understand "restrict commands" as turning on the restrict commands option.

        """)

        # If "restrict commands" mode is on, force the player to mention where to
        # take the object from.
        source += textwrap.dedent("""\
        The taking allowed flag is a truth state that varies.
        The taking allowed flag is usually false.

        Before removing something from something:
            now the taking allowed flag is true.

        After removing something from something:
            now the taking allowed flag is false.

        Before taking a thing (called the object) when the object is on a supporter (called the supporter):
            if the restrict commands option is true and taking allowed flag is false:
                say "Can't see any [object] on the floor! Try taking the [object] from the [supporter] instead.";
                rule fails.

        Before of taking a thing (called the object) when the object is in a container (called the container):
            if the restrict commands option is true and taking allowed flag is false:
                say "Can't see any [object] on the floor! Try taking the [object] from the [container] instead.";
                rule fails.

        Understand "take [something]" as removing it from.

        Rule for supplying a missing second noun while removing:
            if restrict commands option is false and noun is on a supporter (called the supporter):
                now the second noun is the supporter;
            else if restrict commands option is false and noun is in a container (called the container):
                now the second noun is the container;
            else:
                try taking the noun;
                say ""; [Needed to avoid printing a default message.]

        """)

        # Special command to print the version number
        source += textwrap.dedent("""\
        The version number is always {}.

        Reporting the version number is an action applying to nothing.
        Carry out reporting the version number:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            say "[version number]".

        Understand "tw-print version" as reporting the version number.

        """).format(self.VERSION)

        # Special command to print the maximum score of a game.
        source += textwrap.dedent("""\
        Reporting max score is an action applying to nothing.
        Carry out reporting max score:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            say "[maximum score]".

        Understand "tw-print max_score" as reporting max score.

        """)

        # Special command to print the id of an object.
        source += textwrap.dedent("""\
        To print id of (something - thing):
            (- print {something}, "^"; -).

        Printing the id of player is an action applying to nothing.
        Carry out printing the id of player:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            print id of player.

        Printing the id of EndOfObject is an action applying to nothing.
        Carry out printing the id of EndOfObject:
            Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
            print id of EndOfObject.

        Understand "tw-print player id" as printing the id of player.
        Understand "tw-print EndOfObject id" as printing the id of EndOfObject.

        """)

        # Add dummy object to detect end of the objects tree.
        source += textwrap.dedent("""\
            There is a EndOfObject.

        """)

        # Indent using \t instead of spaces because of Inform6.
        while True:
            last = source
            source = re.sub("(^ *)    ", r"\1\t", source, flags=re.MULTILINE)
            if source == last:
                break

        return source


def generate_inform7_source(game: Game, seed: int = 1234, use_i7_description: bool = False) -> str:
    inform7 = Inform7Game(game)
    inform7.use_i7_description = use_i7_description
    return inform7.gen_source(seed=seed)


def compile_inform7_game(source: str, output: str, verbose: bool = False) -> None:
    with make_temp_directory(prefix="tmp_inform") as project_folder:
        filename, ext = os.path.splitext(output)
        story_filename = filename + ".ni"

        # Save story file.
        with open(story_filename, 'w') as f:
            f.write(source)

        # Create the file structure needed by Inform7.
        source_folder = pjoin(project_folder, "Source")
        build_folder = pjoin(project_folder, "Build")
        if not os.path.isdir(source_folder):
            os.makedirs(source_folder)

        shutil.copy(story_filename, pjoin(source_folder, "story.ni"))

        # Write mandatory uuid.txt file
        open(pjoin(project_folder, "uuid.txt"), 'w').close()

        # Build Inform7 -> Inform6 -> game
        INFORM_HOME = os.environ.get("INFORM_HOME", I7_DEFAULT_PATH)
        ni = pjoin(INFORM_HOME, "share", "inform7", "Compilers", "ni")
        i6 = pjoin(INFORM_HOME, "share", "inform7", "Compilers", "inform6")
        i7_internal = pjoin(INFORM_HOME, "share", "inform7", "Internal")

        # Compile story file.
        cmd = [ni, "--internal", i7_internal, "--format={}".format(ext),
               "--project", project_folder]

        if verbose:
            print("Running: {}".format(" ".join(cmd)))

        try:
            stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            msg = ""
            msg += "\n-== ni =-\nFAIL: {}\n{}========\n".format(exc.returncode, exc.output.decode())
            msg += "*** Usually this means a compilation error.\n"
            if ext == ".z8":
                msg += "*** Maybe the game is too big for a .z8 file. Try using .ulx instead.\n"
            msg += "*** See {} for more information.\n".format(story_filename)
            raise CouldNotCompileGameError(msg)
        else:
            if verbose:
                print("-= ni =-\n{}========\n".format(stdout.decode()))

        # Compile inform6 code.
        i6_input_filename = pjoin(build_folder, "auto.inf")

        i6_options = "-"
        # i6_options += "k"  # Debug file, maybe useful to extract vocab?
        if str2bool(os.environ.get("TEXTWORLD_I6_DEBUG", False)):
            i6_options += "D"  # Debug mode, enables Inform7 testing commands.

        i6_options += "E2wS"
        i6_options += "G" if ext == ".ulx" else "v8"
        i6_options += "F0"  # Use extra memory rather than temporary files.
        cmd = [i6, i6_options, i6_input_filename, output]

        if verbose:
            print("Running: {}".format(" ".join(cmd)))

        try:
            stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            msg = ""
            msg += "\n-= i6 =-\nFAIL: {}\n{}========\n".format(exc.returncode, exc.output.decode())
            msg += "*** Usually this means a compilation error.\n"
            if ext == ".z8":
                msg += "*** Maybe the game is too big for a .z8 file. Try using .ulx instead.\n"
            msg += "*** See {} for more information.\n".format(story_filename)
            raise CouldNotCompileGameError(msg)
        else:
            if verbose:
                print("-= i6 =-\n{}========\n".format(stdout.decode()))
