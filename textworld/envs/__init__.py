# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import textworld.envs.wrappers
from textworld.envs.zmachine.frotz import FrotzEnvironment
from textworld.envs.glulx.git_glulx_ml import GitGlulxMLEnvironment as GlulxEnvironment

try:
    from textworld.envs.zmachine.jericho import JerichoEnvironment
except ImportError:
    JerichoEnvironment = None

# Import custom environment
from textworld.envs.zmachine.zork1 import Zork1Environment


CUSTOM_ENVIRONMENTS = {
    # "zork1.z5": Zork1Environment
}
