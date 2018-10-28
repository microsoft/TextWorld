# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import Optional, Mapping, Any, List, Tuple


class GameState:
    """ Representation of the state of a text-based game.

    This object can be used to get additional information about the current
    state of the game.
    """

    def __init__(self, env: Optional["Environment"] = None) -> None:
        """ Create a game state.

        Args:
            env: Environment that can be used to fetch additional information.
        """
        self._env = env
        self._command = None
        self._raw = None
        self.previous_state = None

    def init(self, output: str) -> None:
        """ Initializes the game state from intro text.

        Args:
            output: Text displayed when the game starts.
        """
        self._raw = output

    def update(self, command: str, output: str) -> "GameState":
        """ Creates a new game state with the new information.

        Args:
            command: Command sent to the game's interpreter.
            output: Response from the game's interpreter.

        Returns
            The new state of the game.
        """
        game_state = self.__class__(env=self._env)
        game_state.previous_state = self
        game_state._command = command
        game_state._raw = output
        return game_state

    @property
    def command(self) -> str:
        """ Last command sent to the interpreter. """
        return self._command

    @property
    def feedback(self) -> str:
        """ Interpreter's response after issuing last command. """
        if not hasattr(self, "_feedback"):
            self._feedback = self._raw

        return self._feedback

    @property
    def nb_moves(self) -> int:
        """ Number of actions perfomed up until now. """
        if not hasattr(self, "_nb_moves"):
            node = self
            self._nb_moves = 0
            while node.previous_state is not None:
                node = node.previous_state
                self._nb_moves += 1

        return self._nb_moves

    @property
    def description(self) -> str:
        """ Description at the current location.

        It's usually the output of the "look" command.
        """
        raise NotImplementedError

    @property
    def inventory(self) -> str:
        """ Player's inventory.

        It's usually the output of the "inventory" command.
        """
        raise NotImplementedError

    @property
    def score(self) -> float:
        """ Current score.

        It's usually the output of the "score" command.
        """
        raise NotImplementedError

    @property
    def max_score(self) -> float:
        """ Max score for this game.

        It's usually the output of the "score" command.
        """
        raise NotImplementedError

    @property
    def location(self) -> str:
        """ Name of the current location. """
        raise NotImplementedError

    @property
    def game_ended(self) -> bool:
        """ Whether the game is finished or not. """
        return self.has_won | self.has_lost

    @property
    def has_won(self) -> bool:
        """ Whether the player has won the game or not. """
        raise NotImplementedError

    @property
    def has_lost(self) -> bool:
        """ Whether the player has lost the game or not. """
        raise NotImplementedError

    def __str__(self) -> str:
        return self.feedback


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

    @property
    def metadata(self) -> Mapping:
        """ Environment's metadata.

        For instance, it can contain the supported rendering modes
        `'render.modes': {'human', 'text', 'ansi'}`.
        """
        return {}

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
        if mode not in self.metadata["render.modes"]:
            raise ValueError("Unknown mode: {}".format(mode))

        raise NotImplementedError()

    def close(self) -> None:
        """ Ends the game. """
        pass

    def activate_state_tracking(self) -> None:
        """ Enables state tracking. """
        msg = "State tracking is not supported for environment: {}"
        msg = msg.format(self.__class__.__name__)
        raise NotImplementedError(msg)

    def compute_intermediate_reward(self) -> None:
        """ Enables intermediate reward computation. """
        msg = "State tracking is not supported for environment: {}"
        msg = msg.format(self.__class__.__name__)
        raise NotImplementedError(msg)

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


class Wrapper(Environment):
    """ Special environment that wraps others to provide new functionalities.

    Special environment that wraps other :py:class:`Environment`
    objects to provide new functionalities (e.g. transcript recording, viewer,
    etc).
    """

    def __init__(self, env: Environment) -> None:
        """
        Args:
            env: environment to wrap.
        """
        self._wrapped_env = env

    def __call__(self, env: Environment) -> Environment:
        """
        Args:
            env: environment to wrap.

        Returns:
            The wrapped environment.
        """
        self._wrapped_env = env
        return self

    @property
    def metadata(self) -> Mapping:
        return {}

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        return self._wrapped_env.step(command)

    def reset(self) -> GameState:
        return self._wrapped_env.reset()

    def seed(self, seed: Optional[int] = None) -> List[int]:
        return self._wrapped_env.seed(seed)

    def render(self, mode: str = "human") -> Optional[Any]:
        return self._wrapped_env.render(mode)

    def close(self) -> None:
        return self._wrapped_env.close()

    def activate_state_tracking(self) -> None:
        return self._wrapped_env.activate_state_tracking()

    def compute_intermediate_reward(self) -> None:
        return self._wrapped_env.compute_intermediate_reward()

    @property
    def display_command_during_render(self) -> bool:
        return self._wrapped_env.display_command_during_render()

    @display_command_during_render.setter
    def display_command_during_render(self, value: bool) -> None:
        self._wrapped_env.display_command_during_render = value


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


class GameNotRunningError(RuntimeError):
    """ Error when game is not running (either has terminiated or crashed). """

    def __init__(self):
        msg = ("Game is not running at the moment. Reset the environment to"
               " start a new game using `env.reset()`.")
        super().__init__(msg)
