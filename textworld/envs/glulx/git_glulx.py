# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


# -*- coding: utf-8 -*-
import sys
import textwrap
import subprocess
from pkg_resources import Requirement, resource_filename

from typing import Union

from glk import ffi, lib
from io import StringIO

import textworld
from textworld.core import GameState
from textworld.core import GameNotRunningError

GLULX_PATH = resource_filename(Requirement.parse('textworld'), 'textworld/thirdparty/glulx/Git-Glulx')


def _strip_input_prompt_symbol(text: str) -> str:
    if text.endswith("\n>"):
        return text[:-2]

    return text


class GitGlulxEnv(textworld.Environment):
    """ Environment to support playing Glulx games.

    This environment supports playing text-based games that were compiled for
    the `Glulx virtual machine <https://www.eblong.com/zarf/glulx>`_. The main
    advantage of using Glulx over Z-Machine is it uses 32-bit data and
    addresses, so it can handle game files up to four gigabytes long. This
    comes handy when we want to generate large world with a lot of objects
    in it.

    We use a customized version of `git-glulx <https://github.com/DavidKinder/Git>`_
    as the glulx interpreter. That way we don't rely on stdin/stdout to
    communicate with the interpreter but instead use UNIX sockets.

    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._process = None

    def close(self) -> None:
        if self.game_running:
            self._process.kill()
            self._process.wait()
            self._process = None

        try:
            lib.cleanup_glulx(self._names_struct)
        except AttributeError:
            pass  # Attempted to kill before reset

    def __del__(self):
        self.close()

    def load(self, ulx_file: str) -> None:
        # TODO check file format.
        self.close()  # Terminate existing process if needed.
        self._gamefile = ulx_file

    @property
    def game_running(self) -> bool:
        """ Determines if the game is still running. """
        return self._process is not None and self._process.poll() is None

    def step(self, command: str) -> str:
        if not self.game_running:
            raise GameNotRunningError()

        self.state = GameState()
        self.state.last_command = command.strip()
        self.state.raw = self._send(self.state.last_command)
        if self.state.raw is None:
            raise GameNotRunningError()

        self.state.feedback = _strip_input_prompt_symbol(self.state.raw)
        self.state.score = 0  # Default value.
        self.state.done = False  # Default value.
        return self.state, self.state.score, self.state.done

    def _send(self, command: str) -> Union[str, None]:
        """ Send a command directly to the interpreter.

        This method will not affect the internal state variable.
        """
        if not self.game_running:
            return None

        if len(command) == 0:
            command = " "

        c_command = ffi.new('char[]', command.encode('utf-8'))
        result = lib.communicate(self._names_struct, c_command)
        if result == ffi.NULL:
            self.close()
            return None

        result = ffi.gc(result, lib.free)
        return ffi.string(result).decode('utf-8')

    def reset(self) -> str:
        self.close()  # Terminate existing process if needed.

        self._names_struct = ffi.new('struct sock_names*')

        lib.init_glulx(self._names_struct)
        sock_name = ffi.string(self._names_struct.sock_name).decode('utf-8')
        self._process = subprocess.Popen(["%s/git-glulx-ml" % (GLULX_PATH,), self._gamefile, '-g', sock_name, '-q'])
        c_feedback = lib.get_output_nosend(self._names_struct)
        if c_feedback == ffi.NULL:
            self.close()
            raise ValueError("Game failed to start properly: {}.".format(self._gamefile))
        c_feedback = ffi.gc(c_feedback, lib.free)

        feedback = ffi.string(c_feedback).decode('utf-8')
        feedback = _strip_input_prompt_symbol(feedback)
        self.state = GameState(feedback=feedback, raw=feedback)
        return self.state

    def render(self, mode: str = "human") -> None:
        outfile = StringIO() if mode in ['ansi', "text"] else sys.stdout

        msg = self.state.feedback.rstrip() + "\n"
        if self.display_command_during_render and self.state.last_command is not None:
            msg = '> ' + self.state.last_command + "\n" + msg

        # Wrap each paragraph.
        if mode == "human":
            paragraphs = msg.split("\n")
            paragraphs = ["\n".join(textwrap.wrap(paragraph, width=80)) for paragraph in paragraphs]
            msg = "\n".join(paragraphs)

        outfile.write(msg + "\n")

        if mode == "text":
            outfile.seek(0)
            return outfile.read()

        if mode == 'ansi':
            return outfile
