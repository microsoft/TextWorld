from typing import Iterable, Optional

import numpy as np
import networkx as nx

from textworld.utils import check_modules
from textworld.logic import Proposition

missing_modules = []
try:
    import plotly
    import plotly.graph_objects as go
except ImportError:
    missing_modules.append("plotly")

try:
    import matplotlib.pylab as plt
except ImportError:
    missing_modules.append("matplotlib")


def build_graph_from_facts(facts: Iterable[Proposition]) -> nx.DiGraph:
    """ Builds a graph from a collection of facts.

    Arguments:
        facts: Collection of facts representing a state of a game.

    Returns:
        The underlying graph representation.
    """
    G = nx.DiGraph()
    labels = {}
    for fact in facts:
        # Extract relation triplet from fact (subject, object, relation)
        triplet = (*fact.names, fact.name)
        triplet = triplet if len(triplet) >= 3 else triplet + ("is",)

        src = triplet[0]
        dest = triplet[1]
        relation = triplet[-1]
        if relation in {"is"}:
            # For entity properties and states, we artificially
            # add unique node for better visualization.
            dest = src + "-" + dest

        labels[src] = triplet[0]
        labels[dest] = triplet[1]
        G.add_edge(src, dest, type=triplet[-1])

    nx.set_node_attributes(G, labels, 'label')
    return G


def show_graph(facts: Iterable[Proposition],
               title: str = "Knowledge Graph",
               renderer: Optional[str] = None,
               save: Optional[str] = None) -> "plotly.graph_objs._figure.Figure":

    r""" Visualizes the graph made from a collection of facts.

    Arguments:
        facts: Collection of facts representing a state of a game.
        title: Title for the figure
        renderer:
            Which Plotly's renderer to use (e.g., 'browser').
        save:
            If provided, path where to save a PNG version of the graph.

    Returns:
        The Plotly's figure representing the graph.

    Example:

    >>> import textworld
    >>> options = textworld.GameOptions()
    >>> options.seeds = 1234
    >>> game_file, game = textworld.make(options)
    >>> import gym
    >>> import textworld.gym
    >>> from textworld import EnvInfos
    >>> request_infos = EnvInfos(facts=True)
    >>> env_id = textworld.gym.register_game(game_file, request_infos)
    >>> env = gym.make(env_id)
    >>> _, infos = env.reset()
    >>> textworld.render.show_graph(infos["facts"])

    """
    check_modules(["matplotlib", "plotly"], missing_modules)
    G = build_graph_from_facts(facts)

    plt.figure(figsize=(16, 9))
    pos = nx.drawing.nx_pydot.pydot_layout(G, prog="fdp")

    edge_labels_pos = {}
    trace3_list = []
    for edge in G.edges(data=True):
        trace3 = go.Scatter(
            x=[],
            y=[],
            mode='lines',
            line=dict(width=0.5, color='#888', shape='spline', smoothing=1),
            hoverinfo='none'
        )
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        rvec = (x0 - x1, y0 - y1)  # Vector from dest -> src.
        length = np.sqrt(rvec[0] ** 2 + rvec[1] ** 2)
        mid = ((x0 + x1) / 2., (y0 + y1) / 2.)
        orthogonal = (rvec[1] / length, -rvec[0] / length)

        trace3['x'] += (x0, mid[0] + 0 * orthogonal[0], x1, None)
        trace3['y'] += (y0, mid[1] + 0 * orthogonal[1], y1, None)
        trace3_list.append(trace3)

        offset_ = 5
        edge_labels_pos[(pos[edge[0]], pos[edge[1]])] = (mid[0] + offset_ * orthogonal[0],
                                                         mid[1] + offset_ * orthogonal[1])

    node_x = []
    node_y = []
    node_labels = []
    for node, data in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_labels.append("<b>{}</b>".format(data['label'].replace(" ", "<br>")))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='text',
        text=node_labels,
        textfont=dict(
            family="sans serif",
            size=12,
            color="black"
        ),
        hoverinfo='none',
        marker=dict(
            showscale=True,
            color=[],
            size=10,
            line_width=2
        )
    )

    fig = go.Figure(
        data=[*trace3_list, node_trace],
        layout=go.Layout(
            title=title,
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    def _get_angle(p0, p1):
        x0, y0 = p0
        x1, y1 = p1
        if x1 == x0:
            return 0

        angle = -np.rad2deg(np.arctan((y1 - y0) / (x1 - x0) / (16 / 9)))
        return angle

    def _calc_arrow_standoff(angle, label):
        return 5 + np.log(90 / abs(angle)) * max(map(len, label.split()))

    # Add relation names and relation arrows.
    annotations = []
    for edge in G.edges(data=True):
        p0, p1 = pos[edge[0]], pos[edge[1]]
        x0, y0 = p0
        x1, y1 = p1
        angle = _get_angle(p0, p1)
        annotations.append(
            go.layout.Annotation(
                x=x1,
                y=y1,
                ax=(x0 + x1) / 2,
                ay=(y0 + y1) / 2,
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=3,
                arrowwidth=0.5,
                arrowcolor="#888",
                standoff=_calc_arrow_standoff(angle, G.nodes[edge[1]]['label']),
            )
        )
        annotations.append(
            go.layout.Annotation(
                x=edge_labels_pos[(p0, p1)][0],
                y=edge_labels_pos[(p0, p1)][1],
                showarrow=False,
                text="<i>{}</i>".format(edge[2]['type']),
                textangle=angle,
                font=dict(
                    family="sans serif",
                    size=12,
                    color="blue"
                ),
            )
        )

    fig.update_layout(annotations=annotations)

    if renderer:
        fig.show(renderer=renderer)

    if save:
        fig.write_image(save, width=1920, height=1080, scale=4)

    return fig
