# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld.generator import data


def define_inform7_kinds():
    """ Generate Inform 7 kind definitions. """

    type_defs = ''

    # Making sure we loop through the types hierarchy from the root to the leaves.
    roots = [type for type in data.get_logic().types if len(type.parents) == 0]
    for root in roots:
        for type_ in root.subtypes:
            parent_types = list(type_.parent_types)
            if len(parent_types) == 0:
                continue  # Skip types without a parent.

            kind = data.INFORM7_VARIABLES[type_.name]
            parent_kind = data.INFORM7_VARIABLES[parent_types[0].name]  # The first parent should define the kind of object.

            if kind == "" or parent_kind == "":
                continue

            type_defs += "The {kind} is a kind of {parent_kind}.".format(kind=kind, parent_kind=parent_kind)
            type_definition = data.INFORM7_VARIABLES_DESCRIPTION[type_.name]
            if type_definition:
                type_defs += " " + type_definition

            attributes = {vtype for parent_type in parent_types[1:] for vtype in parent_type.supertypes}
            for attribute in attributes:
                type_defs += " " + data.INFORM7_VARIABLES_DESCRIPTION[attribute.name]

            type_defs += "\n"

    return type_defs
