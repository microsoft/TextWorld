# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


"""
Creates server for streamed game state
"""
import os
import json
from os.path import join as pjoin

from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from threading import Thread
from queue import Queue

import webbrowser
import flask
import gevent
from gevent import pywsgi
import logging
from flask import Flask, request
import pybars

from textworld.envs.glulx.git_glulx_ml import GlulxGameState
from textworld.render import load_state_from_game_state

WEB_SERVER_RESOURCES = pjoin(os.path.abspath(os.path.dirname(__file__)), "tmpl")


def get_html_template(game_state=None):
    # read in template
    compiler = pybars.Compiler()
    with open(pjoin(WEB_SERVER_RESOURCES, 'slideshow.handlebars'), 'r') as f:
        contents = f.read()
        template = compiler.compile(contents)

    if game_state is None:
        return template

    html = template({
        'game_state': game_state,
        'template_path': WEB_SERVER_RESOURCES,
    })
    return html


class ServerSentEvent(object):

    def __init__(self, data: any):
        """
        Object helper to parse dict into SSE data.
        :param data: data to pass to SSE
        """
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data: "data",
            self.event: "event",
            self.id: "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) for k, v in self.desc_map.items() if k]
        return "%s\n\n" % "\n".join(lines)


class SupressStdStreams(object):
    def __init__(self):
        """
        for surpressing std.out streams
        """
        self._null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
        self._save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        os.dup2(self._null_fds[0], 1)
        os.dup2(self._null_fds[1], 2)

    def __exit__(self, *_):
        os.dup2(self._save_fds[0], 1)
        os.dup2(self._save_fds[1], 2)

        for fd in self._null_fds + self._save_fds:
            os.close(fd)


def find_free_port(port_range):
    import socket
    from contextlib import closing

    for port in port_range:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                return s.getsockname()[1]

            except socket.error:
                continue

    raise ValueError("Could not find any available port.")


class VisualizationService(object):
    """
    Server for visualization.

    We instantiate a new process for our flask server, so our game can send updates to
    the server. The server instantiates new gevent Queues for every connection.
    """

    def __init__(self, game_state: GlulxGameState, open_automatically: bool):
        self.prev_state = None
        self.command = None
        self._process = None
        state_dict = load_state_from_game_state(game_state)
        self._history = '<p class="objective-text">{}</p>'.format(game_state.objective.strip().replace("\n", "<br/>"))
        initial_description = game_state.feedback.replace(game_state.objective, "")
        self._history += '<p class="feedback-text">{}</p>'.format(initial_description.strip().replace("\n", "<br/>"))
        state_dict["history"] = self._history
        state_dict["command"] = ""
        self.parent_conn, self.child_conn = Pipe()
        self.game_state = state_dict
        self.open_automatically = open_automatically

    def start_server(self, game_state: dict, port: int, child_conn: Connection):
        """
        function for starting new server on new process.
        :param game_state: initial game state from load
        :param port: port to run server
        :param child_conn: child connection from multiprocessing.Pipe
        """
        server = Server(game_state, port)
        server.start(child_conn)

    def start(self, parent_thread: Thread, port: int) -> None:
        """
        Start visualization server on a new process.
        :param parent_thread: the parent thread that called start.
        :param port: Port to run visualization on.
        """
        def wait_task():
            parent_thread.join()
            self.stop_server()

        # Check if address is available.
        self.port = find_free_port(range(port, port + 100))
        self._process = Process(target=self.start_server, name='flask', args=(self.game_state, self.port, self.child_conn))
        self._process.start()

        thread = Thread(target=wait_task, name='waiting_on_parent_exit')
        thread.start()

        print("Viewer started at http://localhost:{}.".format(self.port))
        if self.open_automatically:
            with SupressStdStreams():
                webbrowser.open("http://localhost:{}/".format(self.port))

    def update_state(self, game_state: GlulxGameState, command: str):
        """
        Propogate state update to server.
        We use a multiprocessing.Pipe to pass state into flask process.
        :param game_state: Glulx game state.
        :param command: previous command
        """
        state_dict = load_state_from_game_state(game_state)
        self._history += '<p class="command-text">> {}</p>'.format(command)
        self._history += '<p class="feedback-text">{}</p>'.format(game_state.feedback.strip().replace("\n", "<br/>"))
        state_dict["command"] = command
        state_dict["history"] = self._history
        self.parent_conn.send(state_dict)

    def stop_server(self):
        self._process.terminate()


class Server(object):
    """
    Visualization server.
    Uses Server-sent Events to update game_state for visualization.
    """

    def __init__(self, game_state: dict, port: int):
        """
        Note: Flask routes are defined in app.add_url_rule in order to
        call `self` in routes.
        :param game_state: game state returned from load_state_from_game_state
        :param port: port to run visualization on
        """
        super(Server, self).__init__()

        # disabling loggers
        log = logging.getLogger('werkzeug')
        log.disabled = True
        self.port = port
        self.results = Queue()
        self.subscribers = []
        self.game_state = game_state
        self.app = Flask(__name__, static_folder=pjoin(WEB_SERVER_RESOURCES, 'static'))

        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/subscribe', 'subscribe', self.subscribe)
        self.slideshow_template = get_html_template()

    def start(self, child_conn: Connection):
        """ Starts the WSGI server and listen for updates on a separate thread.

        :param child_conn: Child connection from `multiprocessing.Pipe`.
        """
        thread = Thread(target=self.listen, name='updates', args=(child_conn, self.results))
        thread.start()

        server = pywsgi.WSGIServer(("0.0.0.0", self.port), self.app, log=None)
        server.serve_forever()

    @staticmethod
    def listen(conn: Connection, results: Queue):
        """
        Listener for updates. Runs on separate thread.
        :param conn: child connection from multiprocessing.Pipe.
        :param results: thread-safe queue for results.
        """
        while True:
            game_state = conn.recv()
            results.put(game_state)

    def update_subscribers(self, game_state: dict):
        """
        Updates all subscribers and updates their data.
        This is for multiple subscribers on the visualization service.
        :param game_state: parsed game_state from load_state_from_game_state
        """
        def notify():
            self.game_state = game_state
            if len(self.subscribers) == 0:
                print("We have no subscribers!")
            else:
                for q in self.subscribers[:]:
                    q.put(game_state)
        gevent.spawn(notify)

    def index(self) -> str:
        """
        Index route ("/").
        Returns HTML template processed by handlebars.
        :return: Flask response object
        """
        output = self.slideshow_template({
            'game_state': json.dumps(self.game_state),
            'template_path': 'http://' + request.host
        })
        resp = flask.Response(output.encode('utf-8'))
        resp.headers['Content-Type'] = 'text/html;charset=utf-8'
        return resp

    def gen(self):
        """
        Our generator for listening for updating state.
        We poll for results to return us something. If nothing is returned then we just pass
        and keep polling.
        :return: yields event-stream parsed data.
        """
        q = gevent.queue.Queue()
        self.subscribers.append(q)
        try:
            while True:
                self.update_subscribers(self.results.get_nowait())
                result = q.get()
                ev = ServerSentEvent(json.dumps(result))
                yield ev.encode()
        except Exception as e:
            pass

    def subscribe(self):
        """
        Our Server-sent Event stream route.
        :return: A stream
        """

        return flask.Response(self.gen(), mimetype='text/event-stream')
