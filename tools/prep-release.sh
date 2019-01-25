#!/usr/bin/env bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

set -ex
echo "Preparing for release...";

# Generate parsers
tatsu textworld/logic/logic.ebnf -o textworld/logic/parser.py -G textworld/logic/model.py
tatsu textworld/textgen/textgen.ebnf -o textworld/textgen/parser.py -G textworld/textgen/model.py
