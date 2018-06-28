# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import re
import os
import sys
import time
from os.path import join as pjoin
from pkg_resources import Requirement, resource_filename

from typing import Optional, List, Tuple

from signal import signal, SIGPIPE, SIG_DFL
from subprocess import PIPE, Popen

from threading import Thread
from queue import Queue, Empty

import textworld
from textworld.core import GameState
from textworld.core import GameNotRunningError

FROTZ_PATH = resource_filename(Requirement.parse('textworld'), 'textworld/thirdparty/frotz')


class DefaultZGameState(GameState):

    @property
    def nb_deaths(self):
        """ Number of times the player has died. """
        return -1

    @property
    def feedback(self):
        """ Interpreter's response after issuing last command. """
        if not hasattr(self, "_feedback"):
            # Extract feeback from command's output.
            self._feedback = self._raw
            if self.previous_state is None:
                # Remove version number and copyright text.
                self._feedback = "\n".join(self._feedback.split("\n")[5:])

        return self._feedback

    @property
    def inventory(self):
        """ Player's inventory. """
        if not hasattr(self, "_inventory"):
            # Issue the "inventory" command and parse its output.
            self._inventory = self._env.send("inventory")

        return self._inventory

    @property
    def score(self):
        """ Current score. """
        return -1

    @property
    def max_score(self):
        """ Max score for this game. """
        return -1

    @property
    def description(self):
        """ Description of the current location. """
        if not hasattr(self, "_description"):
            # Issue the "look" command and parse its output.
            self._description = self._env.send("look")

        return self._description

    @property
    def has_won(self):
        """ Whether the player has won the game or not. """
        return False

    @property
    def has_lost(self):
        """ Whether the player has lost the game or not. """
        return False


class FrotzEnvironment(textworld.Environment):
    """ Environment to support playing Z-Machine games.

    `FrotzEnvironment` relies on the `frotz interpreter
    <http://frotz.sourceforge.net>`_ which is started in a seperate process
    (using the `Python subprocess module
    <https://docs.python.org/3.5/library/subprocess.html)>`_.
    Then, the `FrotzEnvironment` sends text commands via stdin and reads the
    output from stdout. This is known to cause some concurrency issues. For
    that reason :py:class:`textworld.envs.JerichoEnviroment
    <textworld.envs.zmachine.jericho.JerichoEnviroment>` is preferred.
    """

    GAME_STATE_CLASS = DefaultZGameState

    metadata = {'render.modes': ['human', 'ansi', 'text']}

    def __init__(self, game_filename: str) -> None:
        """
        Args:
            game_filename: Path to the game file.
        """
        signal(SIGPIPE, SIG_DFL)
        self.game_name = os.path.splitext(os.path.basename(game_filename))[0]
        self.game_filename = game_filename
        self._seed_value = None
        self._game_process = None

        # Disable some commands.
        self.not_allowed = ["q", "quit", "save", "restore", "restart"]

    def seed(self, seed: Optional[int]) -> List:
        self._seed_value = seed
        return self._seed_value

    def reset(self) -> DefaultZGameState:
        self.close()  # In case, it is running.
        self.game_state = self.GAME_STATE_CLASS(self)

        # Start the game process with both 'standard in' and 'standard out' pipes
        cmd = [pjoin(FROTZ_PATH, 'dfrotz')]
        if self.seed is not None:
            cmd += ['-s', str(self._seed_value)]

        cmd += ['-h', '1000']  # Screen height
        cmd += ['-Z', '0']  # Silence Z-Machine errors.
        cmd += [self.game_filename]

        # Communicate with process in text mode (line buffered),
        # i.e. bufsize=1 which also requires universal_newlines=True.
        self._game_process = Popen(cmd, stdin=PIPE, stdout=PIPE,
                                   bufsize=1, universal_newlines=True)

        # Create Queue object
        self.output_queue = Queue()
        self.last_read = 0
        self.current_line = [[]]

        # Sends buffer from output pipe of game to a queue where it
        # can be retrieved later.
        def _enqueue_pipe_output(stdout, queue):
            # We read one character at the time so we can guess better when
            # frotz has finished writing to stdout, i.e. usually after
            # outputing '>'.
            self.current_line[0] = []

            # While frotz process is still running.
            while self._game_process.poll() is None:
                c = stdout.read(1)
                if c == "":
                    continue

                # print(repr(c))
                self.last_read = time.time()
                self.current_line[0].append(c)

                if c == "\n":
                    # Add complete line to the queue.
                    queue.put("".join(self.current_line[0]))
                    self.current_line[0] = []

            remaining_text = stdout.read()
            stdout.close()
            self.current_line[0].extend(remaining_text)
            queue.put("".join(self.current_line[0]))
            self.current_line[0] = []

        # In another thread keep on reading from frotz's stdout.
        self.thread = Thread(target=_enqueue_pipe_output, args=(self._game_process.stdout, self.output_queue))
        self.thread.daemon = True  # Thread dies with the program
        self.thread.start()

        # Grab start info from game.
        start_output = self._recv()
        self.game_state.init(start_output)
        return self.game_state

    def _extract_first_word(self, text: str) -> str:
        word = ""
        for c in text:
            if not str.isalpha(c) and not str.isdigit(c) and c not in ["'", "-"]:
                break

            word += c

        return word

    def step(self, command: str) -> Tuple[DefaultZGameState, float, bool]:
        command = command.strip()
        first_word = self._extract_first_word(command)
        if first_word in self.not_allowed:
            output = "This command is not allowed!"
        else:
            output = self.send(command)

        self.game_state = self.game_state.update(command, output)
        reward = self.game_state.score
        return self.game_state, reward, self.game_state.game_ended

    def close(self) -> None:
        if self._game_process is not None and self._game_process.poll() is None:
            self._game_process.terminate()
            self.thread.join()

    def _send(self, command: str) -> None:
        if self._game_process.poll() is not None:
            raise GameNotRunningError()

        line = self._read_output(nb_retries=1)

        if len(line) > 0:
            # Make sure we have read everything in stdout before sending a command.
            # Check for concurrency issues.
            raise Exception("***Previous output hasn't been read entirely!!!")

        self._game_process.stdin.write(command + '\n')

    def _read_output(self, nb_retries: int = 30) -> str:
        """ Grab the output from the queue """
        output = ""

        # While there is still output in the queue
        no_retry = 0
        while no_retry < nb_retries:
            try:
                output += self.output_queue.get(timeout=0.0001)
                no_retry = 0  # Reset retry counter.

            except Empty:
                if time.time() - self.last_read < 0.01:
                    continue

                if ">" in self.current_line[0]:
                    break

                no_retry += 1

        output += "".join(self.current_line[0])
        self.current_line[0] = []
        return output

    def _recv(self) -> str:
        output = self._read_output()
        output = re.sub("\n?> *$", "", output)  # Remove input prompt.
        return output

    def send(self, command: str) -> str:
        """ Send a command to the game and return the output.

        Parameters
        ----------
        command : str
            Command to senf to Frotz (Z-machine's interpreter).

        Returns
        -------
        str
            The feeback message of the command sent.
        """
        self._send(command)
        feeback = self._recv()
        return feeback

    def render(self, mode: str = 'human'):
        outfile = io.StringIO() if mode in ['ansi', "text"] else sys.stdout

        if self.display_command_during_render and self.game_state.command is not None:
            command = "> " + self.game_state.command
            outfile.write(command + "\n\n")

        observation = self.game_state.feedback
        outfile.write(observation + "\n")

        if mode == "text":
            outfile.seek(0)
            return outfile.read()

        if mode == 'ansi':
            return outfile
