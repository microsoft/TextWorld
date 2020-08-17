# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from copy import deepcopy
from typing import Optional, Any, List, Tuple, Iterable

import sys
import textwrap
from io import StringIO


class EnvInfos:
    """
    Customizing what information will be returned by an environment.

    Information can be requested by setting one or more attributes to True.
    The attribute `extras` should be a list of strings corresponding to
    keys in the metadata dictionary of TextWorld generated games.

    """

    __slots__ = ['feedback', 'description', 'inventory', 'location',
                 'facts', 'last_action', 'last_command',
                 'game',
                 'won', 'lost',
                 'score', 'moves', 'max_score', 'objective',
                 'entities', 'verbs', 'command_templates',
                 'admissible_commands', 'intermediate_reward',
                 'policy_commands',
                 'extras']

    def __init__(self, **kwargs):
        #: bool: Text observation produced by the game in response to previous command.
        #:       This information changes from one step to another.
        self.feedback = kwargs.get("feedback", False)
        #: bool: Text description of the current room, i.e. output of the
        #:       `look` command.
        #:       This information changes from one step to another.
        self.description = kwargs.get("description", False)
        #: bool: Text listing of the player's inventory, i.e. output of the
        #:       `inventory` command.
        #:       This information changes from one step to another.
        self.inventory = kwargs.get("inventory", False)
        #: bool: Name of the player's current location.
        #:       This information changes from one step to another.
        self.location = kwargs.get("location", False)
        #: bool: All the facts that are currently true about the world.
        #:       This information changes from one step to another.
        self.facts = kwargs.get("facts", False)
        #: bool: The last action performed where `None` means it was not a valid action.
        #:       This information changes from one step to another.
        self.last_action = kwargs.get("last_action", False)
        #: bool: The last command performed where `None` means it was not a valid command.
        #:       This information changes from one step to another.
        self.last_command = kwargs.get("last_command", False)
        #: bool: Current game in its serialized form. Use with `textworld.Game.deserialize`.
        self.game = kwargs.get("game", False)
        #: bool: Whether the player won the game.
        #:       This information changes from one step to another.
        self.won = kwargs.get("won", False)
        #: bool: Whether the player lost the game.
        #:       This information changes from one step to another.
        self.lost = kwargs.get("lost", False)
        #: bool: All commands relevant to the current state.
        #:       This information changes from one step to another.
        self.admissible_commands = kwargs.get("admissible_commands", False)
        #: bool: Sequence of commands leading to a winning state.
        #:       This information changes from one step to another.
        self.policy_commands = kwargs.get("policy_commands", False)
        #: bool: Reward (proxy) indicating if the player is making progress.
        #:       This information changes from one step to another.
        self.intermediate_reward = kwargs.get("intermediate_reward", False)
        #: bool: Number of moves done so far in the game.
        #:       This information changes from one step to another.
        self.moves = kwargs.get("moves", False)
        #: bool: Current score of the game.
        #:       This information changes from one step to another.
        self.score = kwargs.get("score", False)
        #: bool: Maximum reachable score of the game.
        #:       This information *doesn't* change from one step to another.
        self.max_score = kwargs.get("max_score", False)
        #: bool: Objective of the game described in text.
        #:       This information *doesn't* change from one step to another.
        self.objective = kwargs.get("objective", False)
        #: bool: Names of all entities in the game.
        #:       This information *doesn't* change from one step to another.
        self.entities = kwargs.get("entities", False)
        #: bool: Verbs understood by the the game.
        #:       This information *doesn't* change from one step to another.
        self.verbs = kwargs.get("verbs", False)
        #: bool: Templates for commands understood by the the game.
        #:       This information *doesn't* change from one step to another.
        self.command_templates = kwargs.get("command_templates", False)
        #: List[str]: Names of extra information which are game specific.
        self.extras = kwargs.get("extras", [])

        # Check `kwargs` keys are all valid.
        unknown_keys = set(kwargs.keys()) - set(self.__slots__)
        if len(unknown_keys) > 0:
            msg = ("Unknown information requested: {}.".format(sorted(unknown_keys))
                   + " Available information are: {}".format(sorted(self.__slots__)))
            raise ValueError(msg)

    @property
    def basics(self) -> Iterable[str]:
        """ Information requested excluding the extras. """
        return [slot for slot in self.__slots__ if slot != "extras" and getattr(self, slot)]

    def __len__(self) -> int:
        return len(self.basics) + len(self.extras)

    def __eq__(self, other):
        return self.basics == other.basics and self.extras == other.extras

    def copy(self):
        return EnvInfos(**{slot: True for slot in self.basics}, extras=list(self.extras))


class GameState(dict):
    def __getattr__(self, attr):
        return self.get(attr, None)

    def __setattr__(self, attr, value):
        return self.__setitem__(attr, value)

    def copy(self) -> "GameState":
        """ Returns a deepcopy of this game state. """
        state = GameState(self)
        for key in self:
            state[key] = deepcopy(self[key])

        return state


class Environment:
    r""" Class allowing to interact with the game's interpreter.

    The role of an `Environment` is to handle the communication between user
    code and the backend interpreter that manages the text-based game. The
    overall `Environment` structure is highly inspired by `OpenAI's gym
    <https://github.com/openai/gym>`_.

    Example
    -------
    Here's a minimal example of how to interact with an `Environment`

    >>> import textworld
    >>> options = textworld.GameOptions()
    >>> options.seeds = 1234
    >>> options.nb_objects = 5
    >>> options.quest_length = 2
    >>> game_file, _ = textworld.make(options, path='./')  # Generate a random game.
    >>> env = textworld.start(game_file)  # Load the game.
    >>> game_state = env.reset()  # Start a new game.
    >>> env.render()
    I hope you're ready to go into rooms and interact with objects, because you've
    just entered TextWorld! Here is how to play! First thing I need you to do is to
    ensure that the type G chest is open. And then, pick up the keycard from the
    type G chest inside the attic. Got that? Good!
    <BLANKLINE>
    -= Attic =-
    You arrive in an attic. A normal kind of place. You begin to take stock of
    what's in the room.
    <BLANKLINE>
    You make out a type G chest. You can see a TextWorld style locker. The TextWorld
    style locker contains a frisbee and a sock.
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    There is a TextWorld style key on the floor.
    >>> command = "take key"  # Command to send to the game.
    >>> game_state, reward, done = env.step(command)
    >>> env.render()
    (the TextWorld style key)
    You pick up the TextWorld style key from the ground.
    """

    def __init__(self, infos: Optional[EnvInfos] = None) -> None:
        """
        Arguments:
            infos: Information to be included in the game state. By
                       default, only the game's narrative is included.
        """
        self.state = GameState()
        self.infos = infos or EnvInfos()

    def load(self, path: str) -> None:
        """ Loads a new text-based game.

        Arguments:
            path: Path to the game file to load.
        """
        raise NotImplementedError()

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        """ Performs a given command.

        Arguments:
            command: Text command to send to the interpreter.

        Returns:
            A tuple containing the new game state, a reward for performing
            that command and reaching this new state, and whether the game is
            finished or not.
        """
        raise NotImplementedError()

    def reset(self) -> GameState:
        """ Starts game from the beginning.

        Returns:
            Initial state of the game.
        """
        raise NotImplementedError()

    def seed(self, seed: Optional[int] = None) -> None:
        """ Sets the seed for the random number generator. """
        return []

    def render(self, mode: str = "human") -> Optional[str]:
        """ Renders the current state of the game.

        Args:
            mode: The mode to use for rendering.
        """
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

    def close(self) -> None:
        """ Ends the game. """
        pass

    def copy(self) -> "Environment":
        """ Return a copy of this environment at the same state.

        Returns:
            A copy of this environment at the same state.
        """
        raise NotImplementedError()

    @property
    def display_command_during_render(self) -> bool:
        """ Enables/disables displaying the command when rendering. """
        if not hasattr(self, "_display_command_during_render"):
            self.display_command_during_render = False

        return self._display_command_during_render

    @display_command_during_render.setter
    def display_command_during_render(self, value: bool) -> None:
        self._display_command_during_render = value

    def __del__(self) -> None:
        self.close()

    def __str__(self) -> str:
        return self.__class__.__name__


class Wrapper:
    """ Special environment that wraps others to provide new functionalities.

    Special environment that wraps other :py:class:`Environment`
    objects to provide new functionalities (e.g. transcript recording, viewer,
    etc).
    """

    def __init__(self, env: Optional[Environment] = None) -> None:
        """
        Args:
            env: environment to wrap.
        """
        self._wrap(env)

    def __call__(self, env: Environment) -> Environment:
        """
        Args:
            env: environment to wrap.

        Returns:
            The wrapped environment.
        """
        self._wrap(env)
        return self

    def _wrap(self, env) -> None:
        """ Stores reference to the wrapped environment.
        Args:
            env: environment to wrap.
        """
        self._wrapped_env = env

    def __getattr__(self, attr: str):
        _wrapped_env = self.__dict__.get("_wrapped_env")
        if _wrapped_env is None:
            _wrapped_env = getattr(super(), attr, None)

        if _wrapped_env:
            return getattr(_wrapped_env, attr)

        return super().__getattribute__(attr)

    @property
    def unwrapped(self):
        if hasattr(self._wrapped_env, "unwrapped"):
            return self._wrapped_env.unwrapped

        return self._wrapped_env

    def load(self, path: str) -> None:
        return self._wrapped_env.load(path)

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        return self._wrapped_env.step(command)

    def reset(self) -> GameState:
        return self._wrapped_env.reset()

    def seed(self, seed: Optional[int] = None) -> List[int]:
        return self._wrapped_env.seed(seed)

    def render(self, mode: str = "human") -> Optional[Any]:
        return self._wrapped_env.render(mode)

    def close(self) -> None:
        if self._wrapped_env:
            self._wrapped_env.close()

    def copy(self) -> "Wrapper":
        raise NotImplementedError()

    @property
    def display_command_during_render(self) -> bool:
        return self._wrapped_env.display_command_during_render()

    @display_command_during_render.setter
    def display_command_during_render(self, value: bool) -> None:
        self._wrapped_env.display_command_during_render = value

    def __str__(self) -> str:
        return "{}.{}".format(self.__class__.__name__,
                              self._wrapped_env)


class Agent:
    """ Interface for any agent that want to play a text-based game. """

    def reset(self, env: Environment) -> None:
        """ Let the agent set some environment's flags.

        Args:
            env: TextWorld environment.
        """
        pass

    def act(self, game_state: GameState, reward: float, done: bool) -> str:
        """ Acts upon the current game state.

        Args:
            game_state: Current game state.
            reward: Accumulated reward up until now.
            done: Whether the game is finished.

        Returns:
            Text command to be performed in this current state.
        """
        raise NotImplementedError()

    def finish(self, game_state: GameState, reward: float, done: bool) -> None:
        """ Let the agent know the game has finished.

        Args:
            game_state: Game state at the moment the game finished.
            reward: Accumulated reward up until now.
            done: Whether the game has finished normally or not.
                If False, it means the agent's used up all of its actions.
        """
        pass

    @property
    def wrappers(self):
        return []


class GameNotRunningError(RuntimeError):
    """ Error when game is not running (either has terminiated or crashed). """

    def __init__(self):
        msg = ("Game is not running at the moment. Reset the environment to"
               " start a new game using `env.reset()`.")
        super().__init__(msg)


class EnvInfoMissingError(NameError):
    """
    Thrown whenever some environment information EnvInfos.
    """

    def __init__(self, requester, info):
        msg = ("The info '{info}' requested by `{requester}` is missing."
               " Make sure it is enabled like so `Environment(infos=EnvInfos(`{info}`=True))`.")
        super().__init__(msg.format(info=info, requester=requester))
