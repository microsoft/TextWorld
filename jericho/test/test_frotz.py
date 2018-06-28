# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

def test_load_save_file():
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    fname = 'test.qzl'
    if os.path.exists(fname):
        os.remove(fname)
    env.reset()
    orig_obs, _, _, _ = env.step('look')
    env.save(fname)
    new_obs, _, _, _ = env.step('n')
    env.load(fname)
    restored_obs, _, _, _ = env.step('look')
    if os.path.exists(fname):
        os.remove(fname)
    assert orig_obs == restored_obs, "Obs Difference detected: Orig: {} Restored: {}"\
        .format(orig_obs, restored_obs)

def test_load_save_str():
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    env.reset()
    orig_state, _, _, _ = env.step('look')
    save_buff = env.save_str()
    new_state, _, _, _ = env.step('n')
    env.load_str(save_buff)
    restored_state, _, _, _ = env.step('look')
    assert orig_state == restored_state, "State Difference detected: Orig: {} Restored: {}"\
        .format(orig_state, restored_state)

def test_game_over():
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    env.reset()
    env.teleport_player(203)
    obs, score, done, _ = env.step('look')
    assert not done, "Expected to be alive. Instead got obs: {}"\
        .format(obs)
    obs, score, done, _ = env.step('jump')
    assert done, "Expected to be dead. Instead got obs: {}"\
        .format(obs)

def test_self_object():
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    env.reset()
    obs, score, done, _ = env.step('look')
    self_obj = env.get_self()
    assert self_obj.name == 'cretin'
    assert self_obj.num == 4

def test_world_objects():
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    env.reset()
    world_objs = env.get_world_objects()
    zork1_invalid_objs = [82, 247, 249, 251, 252, 253, 254]
    for idx, o in enumerate(world_objs):
        if idx in zork1_invalid_objs:
            assert o is None, "Expected No Object. Got: {}".format(o)
        else:
            assert isinstance(o, ZObject), "Expected ZObject {}. Got {}".format(idx, o)
            assert o.num == idx, "Object num doesn't correspond to idx."

def test_location():
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    env.reset()
    obs, score, done, _ = env.step('look')
    loc = env.get_player_location()
    assert loc.num == 180
    assert loc.child == 4
    obs, score, done, _ = env.step('north')
    print(env.get_player_location())
    loc = env.get_player_location()
    assert loc.num == 81
    assert loc.child == 4

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    print(env.reset())
    obs, score, done, _ = env.step('look')
    world_objs = env.get_world_objects()
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
