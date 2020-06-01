# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import re
from collections import OrderedDict

from textworld.generator.game import Quest, Event, Game

from textworld.generator.text_grammar import Grammar
from textworld.generator.text_grammar import fix_determinant
from textworld.logic import Placeholder


class CountOrderedDict(OrderedDict):
    """ An OrderedDict whose empty items are 0 """

    def __getitem__(self, item):
        if item not in self:
            super().__setitem__(item, 0)
        return super().__getitem__(item)


def assign_new_matching_names(obj1_infos, obj2_infos, grammar, exclude):
    if obj1_infos.name is not None or obj2_infos.name is not None:
        return False  # One of the objects has already a name assigned to it.

    tag = "#({}<->{})_match#".format(obj1_infos.type, obj2_infos.type)
    if not grammar.has_tag(tag):
        return False

    found_matching_names = False
    for _ in range(50):
        result = grammar.expand(tag)
        first, second = result.split("<->")  # Matching arguments are separated by '<->'.

        name1, adj1, noun1 = grammar.split_name_adj_noun(first.strip(), grammar.options.include_adj)
        name2, adj2, noun2 = grammar.split_name_adj_noun(second.strip(), grammar.options.include_adj)
        if name1 not in exclude and name2 not in exclude and name1 != name2:
            found_matching_names = True
            break

    if not found_matching_names:
        msg = ("Not enough variation for '{}'. You can add more variation "
               " in {} or turn on the 'include_adj=True' grammar flag."
               ).format(tag, grammar.obj_grammar_file)
        raise ValueError(msg)

    obj1_infos.name, obj1_infos.adj, obj1_infos.noun = name1, adj1, noun1
    exclude.add(obj1_infos.name)

    obj2_infos.name, obj2_infos.adj, obj2_infos.noun = name2, adj2, noun2
    exclude.add(obj2_infos.name)

    return True


def assign_name_to_object(obj, grammar, game_infos):
    """
    Assign a name to an object (if needed).
    """
    # TODO: use local exclude instead of grammar.used_names
    exclude = grammar.used_names

    obj_infos = game_infos[obj.id]
    if obj_infos.name is not None and not re.match("([a-z]_[0-9]+|P|I)", obj_infos.name):
        return  # The name was already set.

    # Check if the object should match another one (i.e. same adjective).
    if obj.matching_entity_id is not None:
        other_obj_infos = game_infos[obj.matching_entity_id]
        success = assign_new_matching_names(obj_infos, other_obj_infos, grammar, exclude)
        if success:
            return

        # Try swapping the objects around i.e. match(o2, o1).
        success = assign_new_matching_names(other_obj_infos, obj_infos, grammar, exclude)
        if success:
            return

        # TODO: Should we enforce it?
        # Fall back on generating unmatching object name.

    values = grammar.generate_name(obj.type, room_type=obj_infos.room_type, exclude=exclude)
    obj_infos.name, obj_infos.adj, obj_infos.noun = values
    grammar.used_names.add(obj_infos.name)


def assign_description_to_object(obj, grammar, game):
    """
    Assign a descripton to an object.
    """
    if game.infos[obj.id].desc is not None:
        return  # Already have a description.

    # Update the object description
    desc_tag = "#({})_desc#".format(obj.type)
    game.infos[obj.id].desc = ""
    if grammar.has_tag(desc_tag):
        game.infos[obj.id].desc = expand_clean_replace(desc_tag, grammar, obj, game)

    # If we have an openable object, append an additional description
    if game.kb.types.is_descendant_of(obj.type, ["c", "d"]):
        game.infos[obj.id].desc += grammar.expand(" #openable_desc#")


def generate_text_from_grammar(game, grammar: Grammar):
    # Assign a specific room type and name to our rooms
    for room in game.world.rooms:
        # First, generate a unique roomtype and name from the grammar
        if game.infos[room.id].room_type is None and grammar.has_tag("#room_type#"):
            game.infos[room.id].room_type = grammar.expand("#room_type#")

        assign_name_to_object(room, grammar, game.infos)

        # Next, assure objects contained in a room must have the same room type
        for obj in game.world.get_all_objects_in(room):
            if game.infos[obj.id].room_type is None:
                game.infos[obj.id].room_type = game.infos[room.id].room_type

    # Objects in inventory can be of any room type.
    for obj in game.world.get_objects_in_inventory():
        if game.infos[obj.id].room_type is None and grammar.has_tag("#room_type#"):
            game.infos[obj.id].room_type = grammar.expand("#room_type#")

    # Assign name and description to objects.
    for obj in game.world.objects:
        if obj.type in ["I", "P"]:
            continue

        assign_name_to_object(obj, grammar, game.infos)
        assign_description_to_object(obj, grammar, game)

    # Generate the room descriptions.
    for room in game.world.rooms:
        if game.infos[room.id].desc is None:  # Skip rooms which already have a description.
            game.infos[room.id].desc = assign_description_to_room(room, game, grammar)

    # Generate the instructions.
    for quest in game.quests:
        quest.desc = assign_description_to_quest(quest, game, grammar)

    return game


def assign_description_to_room(room, game, grammar):
    """
    Assign a descripton to a room.
    """
    # Add the decorative text
    room_desc = expand_clean_replace("#dec#\n\n", grammar, room, game)

    # Convert the objects into groupings based on adj/noun/type

    objs = [o for o in room.content if game.kb.types.is_descendant_of(o.type, game.kb.types.CLASS_HOLDER)]
    groups = OrderedDict()
    groups["adj"] = OrderedDict()
    groups["noun"] = OrderedDict()

    for obj in objs:
        obj_infos = game.infos[obj.id]
        adj, noun = obj_infos.adj, obj_infos.noun

        # get all grouped adjectives and nouns
        groups['adj'][adj] = list(filter(lambda x: game.infos[x.id].adj == adj, objs))
        groups['noun'][noun] = list(filter(lambda x: game.infos[x.id].noun == noun, objs))

    # Generate the room description, prioritizing group descriptions where possible
    ignore = []
    for obj in objs:
        if obj.id in ignore:
            continue  # Skip that object.

        obj_infos = game.infos[obj.id]
        adj, noun = obj_infos.adj, obj_infos.noun

        if grammar.options.blend_descriptions:
            found = False
            for type in ["noun", "adj"]:
                group_filt = []
                if getattr(obj_infos, type) != "":
                    group_filt = list(filter(lambda x: x.id not in ignore, groups[type][getattr(obj_infos, type)]))

                if len(group_filt) > 1:
                    found = True
                    desc = replace_num(grammar.expand("#room_desc_group#"), len(group_filt))

                    if type == "noun":
                        desc = desc.replace("(val)", "{}s".format(getattr(obj_infos, type)))
                        desc = desc.replace("(name)", obj_list_to_prop_string(group_filt, "adj", game, det_type="one"))
                    elif type == "adj":
                        _adj = getattr(obj_infos, type) if getattr(obj_infos, type) is not None else ""
                        desc = desc.replace("(val)", "{}things".format(_adj))
                        desc = desc.replace("(name)", obj_list_to_prop_string(group_filt, "noun", game))

                    for o2 in group_filt:
                        ignore.append(o2.id)
                        if game.kb.types.is_descendant_of(o2.type, game.kb.types.CLASS_HOLDER):
                            for vtype in [o2.type] + game.kb.types.get_ancestors(o2.type):
                                tag = "#room_desc_({})_multi_{}#".format(vtype, "adj" if type == "noun" else "noun")
                                if grammar.has_tag(tag):
                                    desc += expand_clean_replace(" " + tag, grammar, o2, game)
                                    break

                    room_desc += " {}".format(fix_determinant(desc))
                    break

            if found:
                continue

        if obj.type not in ["P", "I", "d"]:
            for vtype in [obj.type] + game.kb.types.get_ancestors(obj.type):
                tag = "#room_desc_({})#".format(vtype)
                if grammar.has_tag(tag):
                    room_desc += expand_clean_replace(" " + tag, grammar, obj, game)
                    break

    room_desc += "\n\n"

    # Look for potential exit directions.
    exits_with_open_door = []
    exits_with_closed_door = []
    exits_without_door = []
    for dir_ in sorted(room.exits.keys()):
        if dir_ in room.doors:
            door_obj = room.doors[dir_]
            attributes_names = [attr.name for attr in door_obj.get_attributes()]
            if "open" in attributes_names:
                exits_with_open_door.append((dir_, door_obj))
            else:
                exits_with_closed_door.append((dir_, door_obj))
        else:
            exits_without_door.append(dir_)

    exits_desc = []
    # Describing exits with door.
    if grammar.options.blend_descriptions and len(exits_with_closed_door) > 1:
        dirs, door_objs = zip(*exits_with_closed_door)
        e_desc = grammar.expand("#room_desc_doors_closed#")
        e_desc = replace_num(e_desc, len(door_objs))
        e_desc = e_desc.replace("(dir)", list_to_string(dirs, False))
        e_desc = clean_replace_objs(grammar, e_desc, door_objs, game.infos)
        e_desc = repl_sing_plur(e_desc, len(door_objs))
        exits_desc.append(e_desc)

    else:
        for dir_, door_obj in exits_with_closed_door:
            d_desc = expand_clean_replace(" #room_desc_(d)#", grammar, door_obj, game)
            d_desc = d_desc.replace("(dir)", dir_)
            exits_desc.append(d_desc)

    if grammar.options.blend_descriptions and len(exits_with_open_door) > 1:
        dirs, door_objs = zip(*exits_with_open_door)
        e_desc = grammar.expand("#room_desc_doors_open#")
        e_desc = replace_num(e_desc, len(door_objs))
        e_desc = e_desc.replace("(dir)", list_to_string(dirs, False))
        e_desc = clean_replace_objs(grammar, e_desc, door_objs, game.infos)
        e_desc = repl_sing_plur(e_desc, len(door_objs))
        exits_desc.append(e_desc)

    else:
        for dir_, door_obj in exits_with_open_door:
            d_desc = expand_clean_replace(" #room_desc_(d)#", grammar, door_obj, game)
            d_desc = d_desc.replace("(dir)", dir_)
            exits_desc.append(d_desc)

    # Describing exits without door.
    if grammar.options.blend_descriptions and len(exits_without_door) > 1:
        e_desc = grammar.expand("#room_desc_exits#").replace("(dir)", list_to_string(exits_without_door, False))
        e_desc = repl_sing_plur(e_desc, len(exits_without_door))
        exits_desc.append(e_desc)
    else:
        for dir_ in exits_without_door:
            e_desc = grammar.expand("#room_desc_(dir)#").replace("(dir)", dir_)
            exits_desc.append(e_desc)

    room_desc += " ".join(exits_desc)

    # Finally, set the description
    return fix_determinant(room_desc)


class MergeAction:
    """
    Group of actions merged into one.

    This allows for blending consecutive instructions.
    """
    def __init__(self):
        self.name = "ig"
        self.const = []
        self.mapping = OrderedDict()
        self.start = None
        self.end = None


def generate_instruction(action, grammar, game, counts):
    """
    Generate text instruction for a specific action.
    """
    # Get the more precise command tag.
    cmd_tag = "#{}#".format(action.name)
    if not grammar.has_tag(cmd_tag):
        cmd_tag = "#{}#".format(action.name.split("-")[0])

        if not grammar.has_tag(cmd_tag):
            cmd_tag = "#{}#".format(action.name.split("-")[0].split("/")[0])

    separator_tag = "#action_separator_{}#".format(action.name)
    if not grammar.has_tag(separator_tag):
        separator_tag = "#action_separator_{}#".format(action.name.split("-")[0])

        if not grammar.has_tag(separator_tag):
            separator_tag = "#action_separator_{}#".format(action.name.split("-")[0].split("/")[0])

    if not grammar.has_tag(separator_tag):
        separator_tag = "#action_separator#"

    if not grammar.has_tag(separator_tag):
        separator = ""
    else:
        separator = grammar.expand(separator_tag)

    desc = grammar.expand(cmd_tag)

    # We generate a custom mapping.
    mapping = OrderedDict()
    if isinstance(action, MergeAction):
        action_mapping = action.mapping
    else:
        action_mapping = game.kb.rules[action.name].match(action)

    for ph, var in action_mapping.items():
        if var.type == "r":

            # We can use a simple description for the room
            r = game.world.find_room_by_id(var.name)  # Match on 'name'
            if r is None:
                mapping[ph.name] = ''
            else:
                mapping[ph.name] = game.infos[r.id].name
        elif var.type in ["P", "I"]:
            continue
        else:
            # We want a more complex description for the objects
            obj = game.world.find_object_by_id(var.name)
            obj_infos = game.infos[obj.id]

            if grammar.options.ambiguous_instructions:
                assert False, "not tested"
                choices = []

                for t in ["adj", "noun", "type"]:
                    if counts[t][getattr(obj_infos, t)] <= 1:
                        if t == "noun":
                            choices.append(getattr(obj_infos, t))
                        elif t == "type":
                            choices.append(game.kb.types.get_description(getattr(obj_infos, t)))
                        else:
                            # For adj, we pick an abstraction on the type
                            atype = game.kb.types.get_description(grammar.rng.choice(game.kb.types.get_ancestors(obj.type)))
                            choices.append("{} {}".format(getattr(obj_infos, t), atype))

                # If we have no possibilities, use the name (ie. prioritize abstractions)
                if len(choices) == 0:
                    choices.append(obj_infos.name)

                mapping[ph.name] = grammar.rng.choice(choices)
            else:
                mapping[ph.name] = obj_infos.name

    # Replace the keyword with one of the possibilities
    for keyword in re.findall(r'[(]\S*[)]', desc + separator):
        for key in keyword[1:-1].split("|"):
            if key in mapping:
                desc = desc.replace(keyword, mapping[key])
                separator = separator.replace(keyword, mapping[key])

    return desc, separator


def assign_description_to_quest(quest: Quest, game: Game, grammar: Grammar):
    event_descriptions = []
    for event in quest.win_events:
        event_descriptions += [describe_event(event, game, grammar)]

    quest_desc = " OR ".join(desc for desc in event_descriptions if desc)
    return quest_desc


def describe_event(event: Event, game: Game, grammar: Grammar) -> str:
    """
    Assign a descripton to a quest.
    """
    # We have to "count" all the adj/noun/types in the world
    # This is important for using "unique" but abstracted references to objects
    counts = OrderedDict()
    counts["adj"] = CountOrderedDict()
    counts["noun"] = CountOrderedDict()
    counts["type"] = CountOrderedDict()

    # Assign name and description to objects.
    for obj in game.world.objects:
        if obj.type in ["I", "P"]:
            continue

        obj_infos = game.infos[obj.id]
        counts['adj'][obj_infos.adj] += 1
        counts['noun'][obj_infos.noun] += 1
        counts['type'][obj.type] += 1

    if len(event.actions) == 0:
        # We don't need to say anything if the quest is empty
        event_desc = ""
    else:
        # Generate a description for either the last, or all commands
        if grammar.options.only_last_action:
            actions_desc, _ = generate_instruction(event.actions[-1], grammar, game, counts)
            only_one_action = True
        else:
            actions_desc_list = []
            # Decide if we blend instructions together or not
            if grammar.options.blend_instructions:
                instructions = get_action_chains(event.actions, grammar, game)
            else:
                instructions = event.actions

            only_one_action = len(instructions) < 2
            for c in instructions:
                desc, separator = generate_instruction(c, grammar, game, counts)
                actions_desc_list.append(desc)
                if c != instructions[-1] and len(separator) > 0:
                    actions_desc_list.append(separator)
            actions_desc = " ".join(actions_desc_list)

        if only_one_action:
            quest_tag = grammar.get_random_expansion("#quest_one_action#")
            quest_tag = quest_tag.replace("(action)", actions_desc.strip())

        else:
            quest_tag = grammar.get_random_expansion("#quest#")
            quest_tag = quest_tag.replace("(list_of_actions)", actions_desc.strip())

        event_desc = grammar.expand(quest_tag)
        event_desc = re.sub(r"(^|(?<=[?!.]))\s*([a-z])",
                            lambda pat: pat.group(1) + ' ' + pat.group(2).upper(),
                            event_desc)

    return event_desc


def get_action_chains(actions, grammar, game):
    """ Reduce the action list by combining similar actions. """
    seq_lim = -1
    sequences = []

    # Greedily get the collection of sequences
    for size in range(len(actions), 1, -1):
        for start in range(len(actions) - size + 1):
            if start > seq_lim:
                is_sequence, seq = is_seq(actions[start:start + size], game)
                if is_sequence and grammar.has_tag("#{}#".format(seq.name)):
                    seq.start = start
                    seq.end = start + size
                    sequences.append(seq)
                    seq_lim = start + size

    # Now build the reduced list of actions
    final_seq = []
    i = 0
    while (i < len(actions)):
        if len(sequences) > 0 and sequences[0].start == i:
            i = sequences[0].end
            final_seq.append(sequences[0])
            sequences.pop(0)
        else:
            final_seq.append(actions[i])
            i += 1

    return final_seq


def is_seq(chain, game):
    """ Check if we have a theoretical chain in actions. """
    seq = MergeAction()

    room_placeholder = Placeholder('r')

    action_mapping = game.kb.rules[chain[0].name].match(chain[0])
    for ph, var in action_mapping.items():
        if ph.type not in ["P", "I"]:
            seq.mapping[ph] = var
            seq.const.append(var)

    for c in chain:
        c_action_mapping = game.kb.rules[c.name].match(c)

        # Update our action name
        seq.name += "_{}".format(c.name.split("/")[0])

        # We break a chain if we move rooms
        if c_action_mapping[room_placeholder] != seq.mapping[room_placeholder]:
            return False, seq

        # Update the mapping
        for ph, var in c_action_mapping.items():
            if ph.type not in ["P", "I"]:
                if ph in seq.mapping and var != seq.mapping[ph]:
                    return False, seq
                else:
                    seq.mapping[ph] = var

        # Remove any objects that we no longer use
        tmp = list(filter(lambda x: x in c_action_mapping.values(), seq.const))

        # If all original objects are gone, the seq is broken
        if len(tmp) == 0:
            return False, seq

        # Update our obj list
        seq.const = tmp

    return True, seq


def replace_num(phrase, val):
    """ Add a numerical value to a string. """
    if val == 1:
        return phrase.replace("(^)", "one")
    elif val == 2:
        return phrase.replace("(^)", "two")
    else:
        return phrase.replace("(^)", "several")


def expand_clean_replace(symbol, grammar, obj, game):
    """ Return a cleaned/keyword replaced symbol. """
    obj_infos = game.infos[obj.id]
    phrase = grammar.expand(symbol)
    phrase = phrase.replace("(obj)", obj_infos.id)
    phrase = phrase.replace("(name)", obj_infos.name)
    phrase = phrase.replace("(name-n)", obj_infos.noun if obj_infos.adj is not None else obj_infos.name)
    phrase = phrase.replace("(name-adj)", obj_infos.adj if obj_infos.adj is not None else grammar.expand("#ordinary_adj#"))
    if obj.type != "":
        phrase = phrase.replace("(name-t)", game.kb.types.get_description(obj.type))
    else:
        assert False, "Does this even happen?"

    return fix_determinant(phrase)


def clean_replace_objs(grammar, desc, objs, game):
    """ Return a cleaned/keyword replaced for a list of objects. """
    desc = desc.replace("(obj)", obj_list_to_prop_string(objs, "id", game, det=False))
    desc = desc.replace("(name)", obj_list_to_prop_string(objs, "name", game, det=False))
    desc = desc.replace("(name-n)", obj_list_to_prop_string(objs, "noun", game, det=False))
    desc = desc.replace("(name-adj)", obj_list_to_prop_string(objs, "adj", game, det=False))
    desc = desc.replace("(name-definite)", obj_list_to_prop_string(objs, "name", game, det=True, det_type="the"))
    desc = desc.replace("(name-indefinite)", obj_list_to_prop_string(objs, "name", game, det=True, det_type="a"))
    desc = desc.replace("(name-n-definite)", obj_list_to_prop_string(objs, "noun", game, det=True, det_type="the"))
    desc = desc.replace("(name-n-indefinite)", obj_list_to_prop_string(objs, "noun", game, det=True, det_type="a"))
    return desc


def repl_sing_plur(phrase, length):
    """ Alter a sentence depending on whether or not we are dealing
        with plural or singular objects (for counting)
    """
    for r in re.findall(r'[\[][^\[]*\|[^\[]*[\]]', phrase):
        if length > 1:
            phrase = phrase.replace(r, r[1:-1].split("|")[1])
        else:
            phrase = phrase.replace(r, r[1:-1].split("|")[0])
    return phrase


def obj_list_to_prop_string(objs, property, game, det=True, det_type="a"):
    """ Convert an object list to a nl string list of names. """
    return list_to_string(list(map(lambda obj: getattr(game.infos[obj.id], property), objs)), det=det, det_type=det_type)


def list_to_string(lst, det, det_type="a"):
    """ Convert a list to a natural language string. """
    string = ""
    if len(lst) == 1:
        return "{}{}".format(det_type + " " if det else "", lst[0])

    for i in range(len(lst)):
        if i >= (len(lst) - 1):
            string = "{} and {}{}".format(string[:-2], "{} ".format(det_type) if det else "", lst[i])
        else:
            string += "{}{}, ".format("{} ".format(det_type) if det else "", lst[i])
    return string
