# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re
import json
import os
import shutil
import subprocess
import textwrap
from os.path import join as pjoin

from pkg_resources import Requirement, resource_filename

from textworld.utils import make_temp_directory, str2bool

from textworld.generator import data

from textworld.generator.game import Quest
from textworld.logic import Signature
from textworld.generator.inform7.grammar import define_inform7_kinds


I7_DEFAULT_PATH = resource_filename(Requirement.parse('textworld'), 'textworld/thirdparty/inform7-6M62')


class CouldNotCompileGameError(RuntimeError):
    pass


def gen_source_for_map(src_room) -> str:
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
            _, template = data.INFORM7_PREDICATES[sig]
            mapping = {'r': dest_room_id, "r'": src_room_id}
            source += template.format(**mapping) + ".\n"

    return source


def gen_source_for_attribute(attr) -> str:
    pt = data.INFORM7_PREDICATES.get(attr.signature)
    if pt is None:
        return None

    pred, template = pt
    mapping = pred.match(attr)
    mapping = {ph.name: var.name for ph, var in mapping.items()}
    return template.format(**mapping)


def gen_source_for_attributes(attributes) -> str:
    source = ""
    for attr in attributes:
        source_attr = gen_source_for_attribute(attr)
        if source_attr:
            source += source_attr + ".\n"

    return source


def gen_source_for_conditions(conds) -> str:
    """Generate Inform 7 source for winning/losing conditions."""

    i7_conds = []
    for cond in conds:
        i7_cond = gen_source_for_attribute(cond)
        if i7_cond:
            i7_conds.append(i7_cond)

    # HACK: In Inform7 we have to mention a container/door is unlocked AND closed.
    for cond in conds:
        if cond.name == "closed":
            i7_conds.append("the {} is unlocked".format(cond.arguments[0].name))

    return " and ".join(i7_conds)


def gen_source_for_objects(objects, var_infos, use_i7_description=False):
    source = ""
    for obj in objects:
        if obj.type in ["P", "I"]:
            continue  # Skip player

        obj_infos = var_infos[obj.id]
        if not use_i7_description:
            # Describe the object.
            source += 'The description of {} is "{}".\n'.format(obj_infos.id, obj_infos.desc)
            source += 'The printed name of {} is "{}".\n'.format(obj_infos.id, obj_infos.name)

            # Since we use objects' id in Inform7 source code, we need to specify how to refer to them.
            source += 'Understand "{}" as {}.\n'.format(obj_infos.name, obj_infos.id)

            # If an object's name is composed of multiple words, make them all refer to the object.
            words = obj_infos.name.split()
            if len(words) > 1:
                for word in words:
                    if word.lower() not in ["the", "of"]:
                        source += 'Understand "{}" as {}.\n'.format(word, obj_infos.id)

        # List object's attributes
        source += gen_source_for_attributes(obj.get_attributes())

    return source


def gen_commands_from_actions(actions, var_infos):
    def _get_name_mapping(action):
        mapping = data.get_rules()[action.name].match(action)
        return {ph.name: var_infos[var.name].name for ph, var in mapping.items()}

    commands = []
    for action in actions:
        command = "None"
        if action is not None:
            command = data.INFORM7_COMMANDS[action.name]
            command = command.format(**_get_name_mapping(action))

        commands.append(command)

    return commands


def find_action_given_inform7_event(i7_event, actions, var_infos):
    def _get_name_mapping(action):
        mapping = data.get_rules()[action.name].match(action)
        return {ph.name: var_infos[var.name].name for ph, var in mapping.items()}

    for action in actions:
        event = data.INFORM7_EVENTS[action.name]

        if event.format(**_get_name_mapping(action)) == i7_event:
            return action

    return None


def generate_inform7_source(game, seed=1234, use_i7_description=False):
    var_infos = game.infos
    world = game.world
    quests = game.quests

    source = ""
    source += "Use scoring. The maximum score is 1.\n"
    source += "When play begins, seed the random-number generator with {}.\n\n".format(seed)
    source += define_inform7_kinds()
    # Mention that rooms have a special text attribute called 'internal name'.
    source += "A room has a text called internal name.\n\n"

    # Define custom addons.
    source += data.INFORM7_ADDONS_CODE + "\n"

    # Declare all rooms.
    room_names = [room.id for room in world.rooms]
    source += "The " + " and the ".join(room_names) + " are rooms.\n\n"

    # Process the rooms.
    for room in world.rooms:
        room_infos = var_infos[room.id]
        room_name = room_infos.name

        if not use_i7_description:
            # Describe the room.
            room_desc = room_infos.desc
            source += "The internal name of {} is \"{}\".\n".format(room.id, room_name)
            source += "The printed name of {} is \"-= {} =-\".\n".format(room.id, str.title(room_name))

            parts = []
            splits = re.split("\[end if\]", room_desc)
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
        source += gen_source_for_map(room)

    # Declare all objects
    for vtype in data.get_types():
        if vtype in ["P", "I"]:
            continue  # Skip player and inventory.

        entities = world.get_entities_per_type(vtype)
        if len(entities) == 0:
            continue  # No entity of that specific type.

        kind = data.INFORM7_VARIABLES[vtype]
        names = [entity.id for entity in entities]
        source += "The " + " and the ".join(names) + " are {}s.\n".format(kind)
        # All objects are privately-named and we manually define all "Understand as" phrases needed.
        source += "The " + " and the ".join(names) + " are privately-named.\n"

    # Process the objects.
    source += "\n"
    source += gen_source_for_objects(world.objects, var_infos,
                                     use_i7_description=use_i7_description)
    source += "\n\n"

    # Place the player.
    source += "The player is in {}.\n\n".format(var_infos[world.player_room.id].id)

    quest = None
    if len(quests) > 0:
        quest = quests[0]  # TODO: randomly sample a quest.
        commands = gen_commands_from_actions(quest.actions, var_infos)
        quest.commands = commands

        walkthrough = '\nTest me with "{}"\n\n'.format(" / ".join(commands))
        source += walkthrough

        # Add winning and losing conditions.
        ending_condition = """\
        Every turn:
            if {}:
                end the story; [Lost]
            else if {}:
                end the story finally; [Win]

        """

        winning_tests = gen_source_for_conditions(quest.win_action.preconditions)

        losing_tests = "1 is 0 [always false]"
        if quest.fail_action is not None:
            losing_tests = gen_source_for_conditions(quest.fail_action.preconditions)

        ending_condition = ending_condition.format(losing_tests, winning_tests)
        source += textwrap.dedent(ending_condition)

    if not use_i7_description:
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

        """)

        source += textwrap.dedent("""\
        Definition: a direction (called thataway) is viable if the room thataway from the location is a room and the room-or-door thataway from the location is a room.

        After looking:
            if list of viable directions is not empty:
                say "You can also go [list of viable directions] from here.".

        """)

    # Replace default banner with a greeting message and the quest description.
    source += textwrap.dedent("""\
    Rule for printing the banner text:
        say "{objective}[line break]".

    """.format(objective=quest.desc if quest is not None else ""))

    # Simply display *** The End *** when game ends.
    source += textwrap.dedent("""\
    Include Basic Screen Effects by Emily Short.

    Rule for printing the player's obituary:
        if story has ended finally:
            increase score by 1;
            center "*** The End ***";
        else:
            center "*** You lost! ***";
        say paragraph break;
        let X be the turn count;
        if restrict commands option is true:
            let X be the turn count minus one;
        say "You scored [score] out of a possible [maximum score], in [X] turn(s).";
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
        stop.

    """)

    # Refeering to an object by it whole name shouldn't be ambiguous.
    source += textwrap.dedent("""\
    Does the player mean doing something with something (called target):
        if the player's command matches the text printed name of the target:
            it is very likely.

    """)

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
        say "Inventory:[line break]";
        list the contents of the player, with newlines, indented, giving inventory information, including all contents, with extra indentation.

    """)

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
        if the number of entries in L is 1:
            say "There is [L with indefinite articles] on the floor.";
        else if the number of entries in L is greater than 1:
            say "There's [L with indefinite articles] on the floor.";

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

    """)

    source += textwrap.dedent("""\
    An objective is some text that varies. The objective is "{objective}".
    """.format(objective=quest.desc if quest is not None else ""))

    # Special command to print the objective of the game, if any.
    source += textwrap.dedent("""\
    Printing the objective is an action applying to nothing.
    Carry out printing the objective:
        say "[objective]".

    Understand "goal" as printing the objective.

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

    When play begins:
        if print state option is true:
            try printing the entire state;

    Every turn:
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
        say "  look:                                describe the current room[line break]";
        say "  goal:                                print the goal of this game[line break]";
        say "  inventory:                           print player's inventory[line break]";
        say "  go <dir>:                            move the player north, east, south or west[line break]";
        say "  examine <something>:                 examine something more closely[line break]";
        say "  eat <something>:                     eat something edible[line break]";
        say "  open <something>:                    open a door or a container[line break]";
        say "  close <something>:                   close a door or a container[line break]";
        say "  drop <something>:                    drop an object on the floor[line break]";
        say "  take <something>:                    take an object that is on the floor[line break]";
        say "  put <something> on <something>:      place an object on a supporter[line break]";
        say "  take <something> from <something>:   take an object from a container or a supporter[line break]";
        say "  insert <something> into <something>: place an object into a container[line break]";
        say "  lock <something> with <something>:   lock a door or a container with a key[line break]";
        say "  unlock <something> with <something>: unlock a door or a container with a key[line break]";

    Understand "help" as displaying help message.

    """)

    # Disable take/get all.
    source += textwrap.dedent("""\
        Taking all is an action applying to nothing.
        Carry out taking all:
            say "You have to be more specific!".

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

    # Special command to restrict possible actions.
    source += textwrap.dedent("""\
    The restrict commands option is a truth state that varies.
    The restrict commands option is usually false.

    Turning on the restrict commands option is an action applying to nothing.
    Carry out turning on the restrict commands option:
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


def compile_inform7_game(source, output, verbose=False):
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
        if str2bool(os.environ.get("TEXTWORLD_I6_DEBUG", True)):
            i6_options += "D"  # Debug mode, so we can do "actions on" and get Inform7 action events.

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
