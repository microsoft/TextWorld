# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import threading
import sys
from typing import Tuple
from collections import Counter
from copy import deepcopy

from textworld.core import Environment, GameState, Wrapper
from textworld.envs.wrappers.glulx_logger import GlulxLogger
from textworld.render import load_state_from_game_state
from textworld.render import get_current, get_highlighted, get_direction


class HtmlViewer(GlulxLogger):
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
        self.port = port
        self._server = None
        self.game_state = None
        self.open_automatically = open_automatically

        # Rendering requires state tracking.
        self.activate_state_tracking()

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
        prev_log = self.current
        game_state, score, done = super().step(command)

        self.game_state = game_state

        state_dict = load_state_from_game_state(game_state)

        highlighted = get_highlighted(state_dict)
        current_room = get_current(state_dict)

        current_tracking_state = deepcopy(prev_log['tracking'])

        prev_room = current_tracking_state['path'][-1]

        # if we transition to a new room, we need to update counter
        if prev_room != current_room:
            direction = get_direction(prev_room, current_room, state_dict)

            entrance_counter = current_tracking_state['entrance_count']

            if current_room not in entrance_counter:
                entrance_counter[current_room] = Counter()

            entrance_counter[current_room].update([direction])

        current_tracking_state['path'].append(current_room)

        highlighted_dict = current_tracking_state['highlighted']
        for key in highlighted_dict.keys():
            print(highlighted)
            highlighted_dict[key].update(highlighted[key])

        current_tracking_state['room_step_count'].update([current_room])

        state_dict['tracking'] = current_tracking_state

        self.set('tracking', current_tracking_state)

        self._server.update_state(state_dict, current_tracking_state, game_state, command)
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
            from textworld.render.serve import VisualizationService
            state_dict = load_state_from_game_state(game_state)

            starting_room = get_current(state_dict)
            room_step_counter = Counter([starting_room])

            highlight_counters = {'items': Counter(), 'doors': Counter()}

            # we set history of where the agent has been
            tracking = {
                'path': [starting_room],
                'highlighted': highlight_counters,
                'room_step_count': room_step_counter,
                'entrance_count': {starting_room: Counter()}
            }
            self.set('tracking', tracking)

            state_dict['tracking'] = tracking

            self._server = VisualizationService(state_dict, tracking, game_state, self.open_automatically)
            self._server.start(threading.current_thread(), port=self.port)
        except ModuleNotFoundError:
            print("Importing HtmlViewer without installed dependencies. Try running `pip install textworld[vis]`")


        return game_state

    def close(self):
        """
        Close the game.

        In addition to shutting down the game, this closes the local webserver.
        """
        self._stop_server()
        super().close()
