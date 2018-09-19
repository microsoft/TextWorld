# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'remove hat/examine hat/take stethoscope/knock on door/open front door/u/n/get tobacco from slipper/get pipe/get newspaper/read newspaper to holmes/look/look/look/read paper/ask holmes about paper/go to bedroom/open door/w/get lamp/get magnifying glass/inventory'
solution = walkthrough.split('/')

def test_sherlock():
    env = FrotzEnv("../../TextWorld-baselines/games/sherlock.z5", seed=6)
    env.reset()
    for act in solution:
        print(act, env.step(act))

def test_max_score():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    assert env.get_max_score() == 100

def test_load_save_file():
    fname = 'sherlock.qzl'
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    for act in solution[:15]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    # orig_obs = orig_obs[orig_obs.index('You'):]
    for act in solution[15:]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    # restored = restored[restored.index('You'):]
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    for act in solution[:15]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    # orig_obs = orig_obs[orig_obs.index('You'):]
    for act in solution[15:]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    # restored = restored[restored.index('You'):]
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    a = 'Score: '
    print(obs)
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index('\n',idx)])

def manual_moves(env, obs):
    a = 'Saturday   5:'
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index(':00 a.m.',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    for act in solution[:11]:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

def test_move_detection():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    for idx, act in enumerate(solution[:11]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'whistle' in inv_names

def find_score():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    env.step(solution[0])
    for act in solution[1:11]:
        cnt += 1
        obs, _, _, _ = env.step(act)
        score = manual_score(env, obs)
        print(obs, score)
        curr_ram = env.get_ram()
        for idx, v in enumerate(curr_ram):
            if v == score:
                if not idx in d:
                    d[idx] = 1
                else:
                    d[idx] += 1
        old_ram = curr_ram
    s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
    for key, value in s:
        if value/float(cnt) > .9:
            print("{}: {}".format(key, value/float(cnt)))

def find_moves():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution[:3]:
        env.step(solution[2])
    for act in solution[3:10]:
        cnt += 1
        obs, _, _, _ = env.step(act)
        print(obs)
        moves = manual_moves(env, obs)
        print('Moves',moves)
        curr_ram = env.get_ram()
        for idx, v in enumerate(curr_ram):
            if v == moves:
                if not idx in d:
                    d[idx] = 1
                else:
                    d[idx] += 1
        old_ram = curr_ram
    s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
    for key, value in s:
        if value/float(cnt) > .8:
            print("{}: {}".format(key, value/float(cnt)))

# def test_world_change():
#     env = FrotzEnv("../roms/sherlock.z5", seed=6)
#     env.reset()
#     for act in solution:
#         obs, _, _, _ = env.step(act)
#         assert env.world_changed(),\
#             "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
#             .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/sherlock.z5", seed=6)
    print(env.reset())
    obs, score, done, _ = env.step('look')
    for act in solution:
        env.step(act)
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

test_sherlock()
#find_moves()
#find_score()
#viz_objs()
