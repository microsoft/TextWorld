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
            if type_.name not in data.INFORM7_VARIABLES:
                continue

            kind = data.INFORM7_VARIABLES[type_.name]
            for parent in type_.parents:
                parent_kind = data.INFORM7_VARIABLES[parent]
                msg = '{} is a kind of {}.\n'.format(kind, parent_kind)
                type_defs += msg

            desc = data.INFORM7_VARIABLES_DESCRIPTION[type_.name]
            if desc:
                type_defs += desc + '\n'

    return type_defs
