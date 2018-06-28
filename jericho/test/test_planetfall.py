# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'scrub floor/wait/read brochure/wait/wait/scrub floor/scrub floor/z/z/z/go port/get in webbing/z/z/z/z/z/z/z/z/z/z/z/z/z/get out/take kit/open door/u/u/u/u/u/drop id/drop brush/n/ne/e/e/e/s/s/s/s/w/take laser/drop old battery/take pliers/take flask/take metal bar/e/put flask under spout'
solution = walkthrough.split('/')

def test_planetfall():
    env = FrotzEnv("../../TextWorld-baselines/games/planetfall.z3", seed=6)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    assert env.get_max_score() == 80

def test_load_save_file():
    fname = 'planetfall.qzl'
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    env.reset()
    for act in solution[:10]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    orig_obs = orig_obs[orig_obs.index('This is'):]
    for act in solution[10:15]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    restored = restored[restored.index('This is'):]
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    env.reset()
    for act in solution[:10]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    orig_obs = orig_obs[orig_obs.index('This is'):]
    for act in solution[10:15]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    restored = restored[restored.index('This is'):]
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    a = 'Score: '
    print(obs)
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index(' Moves:',idx)])

def manual_moves(env, obs):
    a = 'Moves: '
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index('\n',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    env.reset()
    env.step(solution[0])
    old_score = 0
    for act in solution[1:]:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == old_score
        old_score = score

# def test_move_detection():
#     env = FrotzEnv("../roms/planetfall.z3", seed=6)
#     env.reset()
#     env.step(solution[0])
#     for idx, act in enumerate(solution[1:30]):
#         obs, score, done, info = env.step(act)
#         assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'curved bar' in inv_names

def find_score():
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    env.step(solution[0])
    for act in solution[1:]:
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
    env = FrotzEnv("../roms/planetfall.z3", seed=4)
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

# def test_world_change():
#     env = FrotzEnv("../roms/planetfall.z3", seed=6)
#     env.reset()
#     for act in solution:
#         obs, _, _, _ = env.step(act)
#         assert env.world_changed(),\
#             "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
#             .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/planetfall.z3", seed=6)
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

test_planetfall()
#find_moves()
#find_score()
#viz_objs()
