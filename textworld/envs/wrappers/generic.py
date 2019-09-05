# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from typing import Optional

import textworld

from textworld.core import EnvInfos, Wrapper


class GenericEnvironment(Wrapper):

    def __init__(self, infos: Optional[EnvInfos] = None) -> None:
        super().__init__()
        self.infos = infos

    def load(self, gamefile: str) -> None:
        self._wrap(textworld.start(gamefile, self.infos))
