# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'Z/n/z/give drink to frank/z/z/w/l/take purse/e/n/l/take jar/kill abbey/z/z/z/take jar/put jar in purse/w/take knife/z/z/z/z/z/z/z/z/z/take knife/put knife in purse/se/w/take knife and jar/smear peanut butter on frank/put knife and jar in purse/open closet/plug hair dryer in wall/turn on space heater/turn on hair dryer/e/nw/plug toaster into wall/se/w/plug hair dryer into wall/plug space heater into wall/turn on hair dryer/turn on space heater/e /nw/ plug in toaster/wall/turn on toaster/z/z/z/z/z/z/z/z/turn on toaster/z/z/z/z/z/z/z/z/z/z/z/z/z/z/z/z/z/w/e/take napkin/take napkin/s/order a drink/take celery/wipe celery with napkin/put celery in purse/put celery in purse/put peanut butter on celery/n /w/take knife/w/s/se/spill frink/spill drink/take cocktail/spill sunrise/z/z/z/z/z/yell at abbey/n/w/z/z/take knife/smear peanut butter on celery/put raisins on celery/give celery to barb/se/take dish/I/se/sw/w/take coat/smear peanut butter on frank/e/n/open door'

solution = walkthrough.split('/')

ROM_PATH="/home/matthew/workspace/TextWorld-baselines/games/partyfoul.z8"

def test_partyfoul():
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

test_partyfoul()
#find_moves()
#viz_objs()
