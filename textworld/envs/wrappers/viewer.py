# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import threading
from typing import Tuple

from textworld.core import Environment, GameState, Wrapper
from textworld.render.serve import VisualizationService
from textworld.render import WebdriverNotFoundError


class HtmlViewer(Wrapper):
    def __init__(self, env: Environment, open_automatically=True, port: int = 8080) -> None:
        """
        Wrap a TextWorld environment to provide visualization.

        During a playthrough, the game can be visualized via local webserver
        http://localhost:<port>.

        Parameters
        ----------
        :param env:
            The TextWorld environment to wrap.
        :param port:
            Port to use for the web viewer.
        """
        super().__init__(env)
        self._port = port
        self._server = None
        self.game_state = None
        self.open_automatically = open_automatically

        # Rendering requires some additional information.
        self.infos.game = True
        self.infos.facts = True
        self.infos.inventory = True
        self.infos.objective = True

    @property
    def port(self):
        if self._server:
            return self._server.port

        return self._port

    def _stop_server(self) -> None:
        """
        Stop local webserver (if running).
        """
        if self._server is not None:
            self._server.stop_server()
            self._server = None

    def step(self, command: str) -> Tuple[GameState, float, bool]:
        """
        Perform a game step.

        Parameters
        ----------
        command :
            Text command to send to the game engine.

        Returns
        -------
        game_state :
            Updated game state.
        score :
            Score for reaching this state.
        done :
            Whether the same is done or not.
        """
        game_state, score, done = super().step(command)
        self.game_state = game_state
        self._server.update_state(game_state, command)
        return game_state, score, done

    def reset(self) -> GameState:
        """
        Reset the game.

        Returns
        -------
        Initial game state.
        """
        game_state = super().reset()

        self._stop_server()  # In case it is still running.
        try:
            self._server = VisualizationService(game_state, self.open_automatically)
            self._server.start(threading.current_thread(), port=self._port)
        except WebdriverNotFoundError as e:
            print("Missing dependencies for using HtmlViewer. See 'Visualization' section of TextWorld's README.md")
            raise e

        return game_state

    def close(self):
        """
        Close the game.

        In addition to shutting down the game, this closes the local webserver.
        """
        self._stop_server()
        super().close()
