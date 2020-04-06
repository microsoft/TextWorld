#!/usr/bin/env bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

set -ex
echo "Preparing for release...";

# Generate parsers
tatsu textworld/logic/logic.ebnf -o textworld/logic/parser.py -G textworld/logic/model.py
tatsu textworld/textgen/textgen.ebnf -o textworld/textgen/parser.py -G textworld/textgen/model.py

# Generate parsers for PddlEnv support
tatsu textworld/envs/pddl/logic/logic.ebnf -o textworld/envs/pddl/logic/parser.py -G textworld/envs/pddl/logic/model.py
tatsu textworld/envs/pddl/textgen/textgen.ebnf -o textworld/envs/pddl/textgen/parser.py -G textworld/envs/pddl/textgen/model.py
