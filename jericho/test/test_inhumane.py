# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'get amulet/s/w/get torch/get shovel/e/e/e/e/e/n/dig/put amulet in slot/x note/s/w/w/w/w/s/open toilet/d/push button/w/s/s/take pebble/put pebble on second disk/take cube/north/north/e/e/e/e/open door/e/e/e/take necklace/n/n'
solution = walkthrough.split('/')

def test_inhumane():
    env = FrotzEnv("../../TextWorld-baselines/games/inhumane.z5", seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/inhumane.z5", seed=4)
    assert env.get_max_score() == 300

def test_load_save_file():
    fname = 'inhumane.qzl'
    env = FrotzEnv("../roms/inhumane.z5", seed=4)
    env.reset()
    for act in solution[:5]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    for act in solution[5:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/inhumane.z5", seed=4)
    env.reset()
    for act in solution[:5]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    for act in solution[5:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs

def manual_score(obs):
    a = 'Score: '
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index(' Moves',idx)])


def manual_moves(obs):
    a = 'Moves: '
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index('\n',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(obs) == score

def test_move_detection():
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
    env.reset()
    for idx, act in enumerate(solution[:30]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(obs)

def test_inventory():
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'torch' in inv_names

def find_score():
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        score = manual_score(obs)
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
        print("{}: {}".format(key, value/float(cnt)))

def find_moves():
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        moves = manual_moves(obs)
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
        print("{}: {}".format(key, value/float(cnt)))

def test_world_change():
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
    env.reset()
    for act in solution:
        obs, _, _, _ = env.step(act)
        assert env.world_changed(),\
            "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
            .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/inhumane.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/inhumane.z5", seed=5)
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

test_inhumane()
#find_moves()
#find_score()
#viz_objs()
