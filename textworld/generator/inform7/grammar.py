# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld.generator.data import KB


def define_inform7_kinds():
    """ Generate Inform 7 kind definitions. """

    type_defs = ''

    # Making sure we loop through the types hierarchy from the root to the leaves.
    roots = [type for type in KB.logic.types if len(type.parents) == 0]
    for root in roots:
        for type_ in root.subtypes:
            if type_.name not in KB.inform7_variables:
                continue

            kind = KB.inform7_variables[type_.name]
            for parent in type_.parents:
                parent_kind = KB.inform7_variables[parent]
                msg = '{} is a kind of {}.\n'.format(kind, parent_kind)
                type_defs += msg

            desc = KB.inform7_variables_description[type_.name]
            if desc:
                type_defs += desc + '\n'

    return type_defs
