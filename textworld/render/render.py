# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import json
import tempfile
from os.path import join as pjoin
from typing import Union, Dict, Optional

import numpy as np
import networkx as nx

import textworld
from textworld.logic import Variable, Proposition, Action
from textworld.envs.glulx.git_glulx_ml import GlulxGameState
from textworld.logic import State
from textworld.generator import World, Game
from textworld.utils import maybe_mkdir, get_webdriver

from textworld.generator.game import EntityInfo
from textworld.generator import data


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


def load_state_from_game_state(game_state: GlulxGameState, format: str = 'png', limit_player_view: bool = False) -> dict:
    """
    Generates serialization of game state.

    :param game_state: The current game state to visualize.
    :param format: The graph output format (png, svg, pdf, ...)
    :param limit_player_view: Whether to limit the player's view. Default: False.
    :return: The graph generated from this World
    """
    game_infos = game_state.game_infos
    game_infos["objective"] = game_state.objective
    last_action = game_state.action
    # Create a world from the current state's facts.
    world = World.from_facts(game_state.state.facts)
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

# create state object from world and game_info
def load_state(world: World, game_infos: Optional[Dict[str, EntityInfo]] = None, action: Optional[Action] = None, format: str = 'png', limit_player_view: bool = False) -> dict:
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
    nodes = sorted([room.name for room in world.rooms])
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
    player_room = world.player_room
    if game_infos is None:
        new_game = Game(world, [])
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
        cur_item.portable = data.get_types().is_descendant_of(cur_item.type, "o")
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

    result["connections"] = [{"src": game_infos[e[0]].name, "dest": game_infos[e[1]].name, 'door': _get_door(e[2])} for e in edges]
    result["inventory"] = [inv.__dict__ for inv in inventory_items]

    return result


def take_screenshot(url: str, id: str='graph2'):
    """
    Takes a screenshot of DOM element given its id.
    :param url: URL of webpage to open headlessly.
    :param id: ID of DOM element.
    :return: Image object.
    """
    from PIL import Image

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


def visualize(world: Union[Game, State, GlulxGameState, World],
              interactive: bool = False):
    """
    Show the current state of the world.
    :param world: Object representing a game state to be visualized.
    :param interactive: Whether or not to visualize the state in the browser.
    :return: Image object of the visualization.
    """
    try:
        import webbrowser
        from textworld.render.serve import get_html_template
    except ImportError:
        raise ImportError('Visualization dependencies not installed. Try running `pip install textworld[vis]`')

    if isinstance(world, Game):
        game = world
        state = load_state(game.world, game.infos)
        state["objective"] = game.objective
    elif isinstance(world, GlulxGameState):
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

    image = take_screenshot(url)
    if interactive:
        try:
            webbrowser.open(url)
        finally:
            return image

    return image
