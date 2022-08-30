# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import itertools
import numpy as np
import networkx as nx
from collections import OrderedDict


DIRECTIONS = ["north", "south", "east", "west"]

directions = OrderedDict([((0, 1), 'north'),
                          ((-1, 0), 'west'),
                          ((0, -1), 'south'),
                          ((1, 0), 'east')])


def reverse_direction(direction):
    index = DIRECTIONS.index(direction)
    if index % 2 == 0:
        return DIRECTIONS[index + 1]

    return DIRECTIONS[index - 1]


def xy_diff(x, y):
    return tuple(np.array(y) - np.array(x))


def direction(x, y):
    return directions[xy_diff(x, y)]


def gen_layout(rng, n_nodes=5, h=10, w=10):
    '''
    Generate a map with n_nodes rooms by
    picking a subgraph from a h,w grid.
    '''
    G = nx.grid_2d_graph(h, w, create_using=nx.Graph())
    new_G = nx.Graph()
    pos = (rng.randint(0, h - 1),
           rng.randint(0, w - 1))
    visited = set()
    visited.add(pos)
    new_G.add_node(pos, name="r_{}".format(len(new_G)))
    while len(visited) < n_nodes:
        pos_ = pos
        neighbors = G[pos]
        neighbors = list(neighbors.keys())
        pos = neighbors[rng.randint(0, len(neighbors))]
        visited.add(pos)
        if pos not in new_G.nodes:
            new_G.add_node(pos, name="r_{}".format(len(new_G)))

        new_G.add_edge(pos_, pos,
                       has_door=False,
                       door_state=None,
                       door_name=None)
    return new_G


def mark_doors(G, rng, possible_door_states=["open", "closed", "locked"]):
    """Put doors between neighbouring articulation points."""
    components = list(nx.articulation_points(G))
    combos = list(itertools.combinations(components, 2))

    door_id = 0
    for i, j in combos:
        if G.has_edge(i, j):
            door_name = 'd_{}'.format(door_id)
            G[i][j]['has_door'] = True
            G[j][i]['has_door'] = True
            door_state = rng.choice(possible_door_states)
            G[j][i]['door_state'] = door_state
            G[i][j]['door_state'] = door_state
            G[i][j]['door_name'] = door_name
            G[j][i]['door_name'] = door_name
            door_id += 1
            if door_state == "locked":
                G[i][j]["weight"] = 999
                G[j][i]["weight"] = 999
            else:
                G[i][j]["weight"] = 0.1
                G[j][i]["weight"] = 0.1

    return G


def extremes(G):
    '''Find left most and bottom nodes in the cartesian sense.'''
    left_most = sorted(G.nodes(), key=lambda x: x[0])[0]
    bottom = sorted(G.nodes(), key=lambda x: x[1])[0]
    return left_most, bottom


def relabel(G):
    """
    Relabel G so that its origin is (0, 0)
    """
    left_most, bottom = extremes(G)
    x = left_most[0]
    y = bottom[1]
    G = nx.relabel_nodes(G, mapping=lambda n: (n[0] - x, n[1] - y))
    return G


def get_path(G, room1, room2):
    sp = nx.shortest_path(G, source=room1, target=room2)
    return list(zip(sp, sp[1:]))


def plot_graph(G: nx.Graph, show: bool = True) -> None:
    """
    Plot TextWorld's graph representation of a world.
    """
    import matplotlib.pyplot as plt

    pos = {n: n for n in G}
    start = [n for n, d in G.nodes.items() if d.get("start")]

    labels = {n: d.get("name", d.get("id", "")) for n, d in G.nodes.items()}
    node_color = None
    if start:
        node_color = [len(shortest_path(G, start[0], node)) for node in G]
        nx.draw_networkx_nodes(G, nodelist=[start[0]], pos=pos, node_shape="s", node_color=[0], cmap=plt.cm.plasma)

    nx.draw(G, pos=pos, with_labels=False, node_color=node_color, cmap=plt.cm.plasma)
    description = nx.draw_networkx_labels(G, pos, labels=labels)
    for _, t in description.items():
        t.set_position(np.array(t.get_position()) + (0, 0.4))
        t.set_rotation(-25 * 360.0 / (2.0 * np.pi))
        t.set_clip_on(False)

    # Adjust axis.
    min_ = np.min(list(G), axis=0)
    max_ = np.max(list(G), axis=0)
    plt.axis('off')
    plt.xlim([min_[0] - 0.5, max_[0] + 0.5])
    plt.ylim([min_[1] - 0.5, max_[1] + 1])

    if show:
        plt.gcf().set_facecolor("white")
        plt.show()


def create_map(rng, n_nodes, h, w, possible_door_states=["open", "closed", "locked"]):
    G = gen_layout(rng, n_nodes=n_nodes, h=h, w=w)
    if possible_door_states is not None:
        G = mark_doors(G, rng, possible_door_states)

    return G


def create_small_map(rng, n_rooms, possible_door_states=["open", "closed", "locked"]):
    G = nx.grid_2d_graph(3, 3)

    G = nx.Graph()
    room0 = (0, 0)
    G.add_node(room0, name="r_0")

    D = list(directions.keys())
    for i in range(n_rooms - 1):
        rng.shuffle(D)
        new_room = D.pop()
        G.add_node(new_room, name="r_{}".format(len(G)))
        has_door = rng.rand() < 0.5
        door_state = rng.choice(possible_door_states)

        G.add_edge(room0, new_room,
                   has_door=has_door,
                   door_state=door_state if has_door else None,
                   door_name="d_{}".format(i))
        G.add_edge(new_room, room0,
                   has_door=has_door,
                   door_state=door_state if has_door else None,
                   door_name="d_{}".format(i))

    return G


def shortest_path(G, source, target):
    """
    Return shortest path in terms of directions.
    """
    d = []
    path = nx.algorithms.shortest_path(G, source, target)
    for i in range(len(path) - 1):
        d.append(direction(path[i], path[i + 1]))

    return d
