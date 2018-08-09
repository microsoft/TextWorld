# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'GET MASK/WEAR MASK/X MASK/X SELF/DOWN/X LIGHT/X LEAF/X KITE/X COMB/X SHADOW/GET DAGGER/N/GET COMB/X COMB/HIT COMB/X COMPASS/X FEATHER/X HAWK/X SWALLOW/X CRANE/SET COMPASS TO HAWK/LOOK/X TREES/X LEAF/GET LEAF/UNFOLD LEAF/I/X CRANE/SET COMPASS TO CRANE/GET FAN/X FAN/CUT BLUE TASSEL/I/ATTACH PAPER TO TEETH/I/ATTACH STRING TO KITE/SET COMPASS TO SWALLOW/FLY KITE/S/U/LOOK UP/X HORSE/X FLOWER/D/N/W/X BONES/GET BONES WITH CHOPSTICKS/D/X ARRANGEMENT/SET CONSTELLATIONS TO HORSE/X ARRANGEMENT/DOWN/X HAWKS/S/WEAR MASK/LOOK/UP/X STORM/UP'

solution = walkthrough.split('/')

ROM_PATH="/home/matthew/workspace/TextWorld-baselines/games/moonlit.z5"

def test_moonlit():
    env = FrotzEnv(ROM_PATH, seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def find_moves():
    env = FrotzEnv(ROM_PATH, seed=4)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        print(obs)
        curr_ram = env.get_ram()
        diff = np.nonzero(old_ram - curr_ram)[0]
        for j in diff:
            if not j in d:
                d[j] = 1
            else:
                d[j] += 1
        old_ram = curr_ram
    s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
    for key, value in s:
        print("{}: {}".format(key, value/float(cnt)))

def viz_objs():
    import pydot
    env = FrotzEnv(ROM_PATH, seed=5)
    print(env.reset())
    obs, score, done, _ = env.step('look')
    # world_objs = [env.get_object(i) for i in range(175)]
    world_objs = env.get_world_objects()
    for idx, o in enumerate(world_objs):
        print(idx, o)
    graph = pydot.Dot(graph_type='digraph')
    node2graph = {}
    for o in world_objs:
        if o and o.num > 0:
            graph_node = pydot.Node("{} {}\np{} s{} c{}".format(o.num, o.name, o.parent, o.sibling, o.child))
            if o.child <= 0:
                graph_node.add_style("filled")
            graph.add_node(graph_node)
            node2graph[o.num] = graph_node
    for o in world_objs:
        if o and o.num > 0:
            graph_node = node2graph[o.num]
            if o.sibling in node2graph:
                graph_sibling = node2graph[o.sibling]
                graph.add_edge(pydot.Edge(graph_node, graph_sibling, arrowhead='diamond'))
            if o.child in node2graph:
                child = node2graph[o.child]
                graph.add_edge(pydot.Edge(graph_node, child, color='blue'))
    graph.write_pdf('graph.pdf')

test_moonlit()
#find_moves()
#viz_objs()
