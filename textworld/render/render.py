# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import os
import time
import json
import tempfile
from os.path import join as pjoin
from typing import Union, Dict, Optional

import numpy as np
import networkx as nx

from textworld.core import GameState
from textworld.logic import Proposition, Action
from textworld.logic import State
from textworld.generator import World, Game
from textworld.utils import maybe_mkdir, check_modules

from textworld.generator.game import EntityInfo
from textworld.generator.data import KnowledgeBase

from textworld.render.serve import get_html_template

# Try importing optional libraries.
missing_modules = []
try:
    import webbrowser
except ImportError:
    missing_modules.append("webbrowser")

try:
    from PIL import Image
except ImportError:
    missing_modules.append("pillow")

try:
    from selenium import webdriver
except ImportError:
    missing_modules.append("selenium")


XSCALE, YSCALE = 6, 3


# noinspection PyShadowingBuiltins
class GraphItem(object):
    def __init__(self, type, name):
        self.type = type
        self.name = name
        self.contents = []
        self.ocl = ''
        self.predicates = []
        self._infos = ""
        self.highlight = False
        self.portable = False

    @property
    def infos(self):
        if self._infos == "" and len(self.predicates) > 0:
            return ": ({})".format(", ".join(self.predicates))

        return self._infos

    @infos.setter
    def infos(self, value):
        self._infos = value

    def add_content(self, content):
        self.contents.append(content)

    def set_open_closed_locked(self, status):
        self.ocl = status

    def add_unknown_predicate(self, predicate: Proposition):
        self.predicates.append(str(predicate))

    def to_dict(self):
        res = self.__dict__
        res["contents"] = [item.to_dict() for item in res["contents"]]
        return res

    def get_max_depth(self):
        """
        Returns the maximum nest depth of this plus all children. A container with no items has 1 depth,
        a container containing one item has 2 depth, a container containing a container which contains an item
        has 3 depth, and so on.
        :return: maximum nest depth
        """
        if len(self.contents) == 0:
            return 1
        return 1 + max([content.get_max_depth() for content in self.contents])


class GraphRoom(object):
    def __init__(self, name: str, base_room):
        self.name = name
        self.base_room = base_room
        self.items = []
        self.position = None
        self.scale = 4

    def position_string(self) -> str:
        return '%s,%s!' % (self.position[0] * XSCALE, self.position[1] * YSCALE)

    def add_item(self, item) -> None:
        self.items.append(item)


def load_state_from_game_state(game_state: GameState, format: str = 'png', limit_player_view: bool = False) -> dict:
    """
    Generates serialization of game state.

    :param game_state: The current game state to visualize.
    :param format: The graph output format (png, svg, pdf, ...)
    :param limit_player_view: Whether to limit the player's view. Default: False.
    :return: The graph generated from this World
    """
    game_infos = game_state.game.infos
    game_infos["objective"] = game_state.objective  # TODO: should not modify game.infos inplace!
    last_action = game_state.last_action
    # Create a world from the current state's facts.
    world = World.from_facts(game_state._facts)
    return load_state(world, game_infos, last_action, format, limit_player_view)


def temp_viz(nodes, edges, pos, color=[]):
    nodes = [n for n in nodes if n in pos]
    edges = [e for e in edges if e[0] in pos and e[1] in pos]

    import matplotlib.pyplot as plt
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    nx.draw(G, pos)
    for c in color:
        if c in nodes:
            nx.draw_networkx_nodes(G, pos,
                                   nodelist=[c],
                                   node_color='b',
                                   node_size=500,
                                   alpha=0.8)
    plt.show()


def load_state(world: World,
               game_infos: Optional[Dict[str, EntityInfo]] = None,
               action: Optional[Action] = None,
               format: str = 'png',
               limit_player_view: bool = False) -> dict:
    """
    Generates serialization of game state.

    :param world: The current state of the world to visualize.
    :param game_infos: The mapping needed to get objects names.
    :param action: If provided, highlight the world changes made by that action.
    :param format: The graph output format (gv, svg, png...)
    :param limit_player_view: Whether to limit the player's view (defaults to false)
    :return: The graph generated from this World
    """

    if world.player_room is None:
        room = world.rooms[0]
    else:
        room = world.player_room

    edges = []
    pos = {room.name: (0, 0)}

    def used_pos():
        pos_along_edges = []
        for e in edges:
            A, B = pos[e[0]], pos[e[1]]
            if A[0] == B[0]:  # Y-axis edge.
                for i in range(A[1], B[1], np.sign(B[1] - A[1])):
                    pos_along_edges.append((A[0], i))
            else:  # X-axis edge.
                for i in range(A[0], B[0], np.sign(B[0] - A[0])):
                    pos_along_edges.append((i, A[1]))

        return list(pos.values()) + pos_along_edges

    openset = [room]
    closedset = set()

    # temp_viz(nodes, edges, pos, color=[world.player_room.name])
    while len(openset) > 0:
        room = openset.pop(0)
        closedset.add(room)

        for exit, target in room.exits.items():
            if target in openset or target in closedset:
                edges.append((room.name, target.name, room.doors.get(exit)))
                continue

            openset.append(target)

            src_pos = np.array(pos[room.name])
            if exit == "north":
                target_pos = tuple(src_pos + (0, 1))
                if target_pos in used_pos():
                    for n, p in pos.items():
                        if p[1] <= src_pos[1]:
                            pos[n] = (p[0], p[1] - 1)

                pos[target.name] = (pos[room.name][0], pos[room.name][1] + 1)

            elif exit == "south":
                target_pos = tuple(src_pos + (0, -1))
                if target_pos in used_pos():
                    for n, p in pos.items():
                        if p[1] >= src_pos[1]:
                            pos[n] = (p[0], p[1] + 1)

                pos[target.name] = (pos[room.name][0], pos[room.name][1] - 1)

            elif exit == "east":
                target_pos = tuple(src_pos + (1, 0))
                if target_pos in used_pos():
                    for n, p in pos.items():
                        if p[0] <= src_pos[0]:
                            pos[n] = (p[0] - 1, p[1])

                pos[target.name] = (pos[room.name][0] + 1, pos[room.name][1])

            elif exit == "west":
                target_pos = tuple(src_pos + (-1, 0))
                if target_pos in used_pos():
                    for n, p in pos.items():
                        if p[0] >= src_pos[0]:
                            pos[n] = (p[0] + 1, p[1])

                pos[target.name] = (pos[room.name][0] - 1, pos[room.name][1])

            edges.append((room.name, target.name, room.doors.get(exit)))
            # temp_viz(nodes, edges, pos, color=[world.player_room.name])

    rooms = {}
    if game_infos is None:
        new_game = Game(world)
        game_infos = new_game.infos
        for k, v in game_infos.items():
            if v.name is None:
                v.name = k

    pos = {game_infos[k].name: v for k, v in pos.items()}

    for room in world.rooms:
        rooms[room.id] = GraphRoom(game_infos[room.id].name, room)

    result = {}
    # Objective
    if "objective" in game_infos:
        result["objective"] = game_infos["objective"]
        del game_infos["objective"]  # TODO: objective should not be part of game_infos in the first place.

    # Objects
    all_items = {}
    inventory_items = []
    objects = world.objects
    # if limit_player_view:
    #     objects = world.get_visible_objects_in(world.player_room)
    #     objects += world.get_objects_in_inventory()

    # add all items first, in case properties are "out of order"
    for obj in objects:
        cur_item = GraphItem(obj.type, game_infos[obj.id].name)
        cur_item.portable = KnowledgeBase.default().types.is_descendant_of(cur_item.type, "o")
        all_items[obj.id] = cur_item

    for obj in sorted(objects, key=lambda obj: obj.name):
        cur_item = all_items[obj.id]
        for attribute in obj.get_attributes():
            if action and attribute in action.added:
                cur_item.highlight = True

            if attribute.name == 'in':
                # add object to inventory
                if attribute.arguments[-1].type == 'I':
                    inventory_items.append(cur_item)
                elif attribute.arguments[0].name == obj.id:
                    # add object to containers if same object
                    all_items[attribute.arguments[1].name].add_content(cur_item)
                else:
                    print('DEBUG: Skipping attribute %s for object %s' % (attribute, obj.id))

            elif attribute.name == 'at':
                # add object to room
                if attribute.arguments[-1].type == 'r':
                    rooms[attribute.arguments[1].name].add_item(cur_item)
            elif attribute.name == 'on':
                # add object to supporters
                all_items[attribute.arguments[1].name].add_content(cur_item)
            elif attribute.name == 'open':
                cur_item.set_open_closed_locked('open')
            elif attribute.name == 'closed':
                cur_item.set_open_closed_locked('closed')
            elif attribute.name == 'locked':
                cur_item.set_open_closed_locked('locked')
                if not limit_player_view:
                    cur_item.infos = " (locked)"
            elif attribute.name == 'match':
                if not limit_player_view:
                    cur_item.infos = " (for {})".format(game_infos[attribute.arguments[-1].name].name)
            else:
                cur_item.add_unknown_predicate(attribute)

    for room in rooms.values():
        room.position = pos[room.name]

    result["rooms"] = []
    for room in rooms.values():
        room.items = [item.to_dict() for item in room.items]
        temp = room.base_room.serialize()
        temp["attributes"] = [a.serialize() for a in room.base_room.get_attributes()]
        room.base_room = temp
        result["rooms"].append(room.__dict__)

    def _get_door(door):
        if door is None:
            return None

        return all_items[door.name].__dict__

    def _get_name(entity):
        return game_infos[entity].name
    result["connections"] = [{"src": _get_name(e[0]), "dest": _get_name(e[1]), "door": _get_door(e[2])}
                             for e in edges]
    result["inventory"] = [inv.__dict__ for inv in inventory_items]

    return result


def take_screenshot(url: str, id: str = 'world'):
    """
    Takes a screenshot of DOM element given its id.
    :param url: URL of webpage to open headlessly.
    :param id: ID of DOM element.
    :return: Image object.
    """
    check_modules(["pillow"], missing_modules)
    driver = get_webdriver()

    driver.get(url)
    svg = driver.find_element_by_id(id)
    location = svg.location
    size = svg.size
    png = driver.get_screenshot_as_png()

    driver.close()
    image = Image.open(io.BytesIO(png))
    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    image = image.crop((left, top, right, bottom))
    return image


def concat_images(*images):
    check_modules(["pillow"], missing_modules)

    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    return new_im


class WebdriverNotFoundError(Exception):
    pass


def which(program):
    """
    helper to see if a program is in PATH
    :param program: name of program
    :return: path of program or None
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def get_webdriver(path=None):
    """
    Get the driver and options objects.
    :param path: path to browser binary.
    :return: driver
    """
    check_modules(["selenium", "webdriver"], missing_modules)

    def chrome_driver(path=None):
        import urllib3
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('headless')
        options.add_argument('ignore-certificate-errors')
        options.add_argument("test-type")
        options.add_argument("no-sandbox")
        options.add_argument("disable-gpu")
        options.add_argument("allow-insecure-localhost")
        options.add_argument("allow-running-insecure-content")

        if path is not None:
            options.binary_location = path

        SELENIUM_RETRIES = 10
        SELENIUM_DELAY = 3  # seconds
        for _ in range(SELENIUM_RETRIES):
            try:
                return webdriver.Chrome(chrome_options=options)
            except urllib3.exceptions.ProtocolError:  # https://github.com/SeleniumHQ/selenium/issues/5296
                time.sleep(SELENIUM_DELAY)

        raise ConnectionResetError('Cannot connect to Chrome, giving up after {SELENIUM_RETRIES} attempts.')

    def firefox_driver(path=None):
        from selenium.webdriver.firefox.options import Options
        options = Options()
        options.add_argument('headless')
        driver = webdriver.Firefox(firefox_binary=path, options=options)
        return driver

    driver_mapping = {
        'geckodriver': firefox_driver,
        'chromedriver': chrome_driver,
        'chromium-driver': chrome_driver
    }

    for driver in sorted(driver_mapping.keys()):
        found = which(driver)
        if found is not None:
            return driver_mapping.get(driver, None)(path)

    raise WebdriverNotFoundError("Chrome/Chromium/FireFox Webdriver not found.")


def visualize(world: Union[Game, State, GameState, World],
              interactive: bool = False):
    """
    Show the current state of the world.
    :param world: Object representing a game state to be visualized.
    :param interactive: Whether or not to visualize the state in the browser.
    :return: Image object of the visualization.
    """
    check_modules(["webbrowser"], missing_modules)

    if isinstance(world, Game):
        game = world
        state = load_state(game.world, game.infos)
        state["objective"] = game.objective
    elif isinstance(world, GameState):
        state = load_state_from_game_state(game_state=world)
    elif isinstance(world, World):
        state = load_state(world)
    elif isinstance(world, State):
        state = world
        world = World.from_facts(state.facts)
        state = load_state(world)
    else:
        raise ValueError("Don't know how to visualize: {!r}".format(world))

    state["command"] = ""
    state["history"] = ""
    html = get_html_template(game_state=json.dumps(state))
    tmpdir = maybe_mkdir(pjoin(tempfile.gettempdir(), "textworld"))
    fh, filename = tempfile.mkstemp(suffix=".html", dir=tmpdir, text=True)
    url = 'file://' + filename
    with open(filename, 'w') as f:
        f.write(html)

    img_graph = take_screenshot(url, id="world")
    img_inventory = take_screenshot(url, id="inventory")
    image = concat_images(img_inventory, img_graph,)

    if interactive:
        try:
            webbrowser.open(url)
        finally:
            return image

    return image
