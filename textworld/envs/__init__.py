# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.
import re

from textworld.envs.glulx.git_glulx import GitGlulxEnv
from textworld.envs.zmachine.jericho import JerichoEnv
from textworld.envs.tw import TextWorldEnv
from textworld.envs.wrappers.tw_inform7 import TWInform7
from textworld.envs.pddl import PddlEnv


def _guess_backend(path):
    # Guess the backend from the extension.
    if path.endswith(".ulx"):
        return GitGlulxEnv
    elif re.search(r"\.z[1-8]", path):
        return JerichoEnv
    elif path.endswith(".tw-pddl"):
        return PddlEnv

    msg = "Unsupported game format: {}".format(path)
    raise ValueError(msg)
