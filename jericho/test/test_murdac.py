# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 's/s/take key/w/take plank/take rod/e/n/e/w/n/dig/take lamp/s/read grave/e/e/sing guron/take sword/w/unlock door/open door/n/close door/lock door/drop key/d/w/w/score'
solution = walkthrough.split('/')

def test_murdac():
    env = FrotzEnv("../../TextWorld-baselines/games/murdac.z5", seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    assert env.get_max_score() == 250

def test_load_save_file():
    fname = 'murdac.qzl'
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    for act in solution[:4]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    for act in solution[4:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    for act in solution[:4]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    for act in solution[4:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    print("Original",orig_obs)
    print("Restored",restored)
    assert restored == orig_obs

def manual_score(env):
    obs, _, _, _ = env.step('score')
    # print(obs)
    pattern = 'you will have scored '
    start = obs.index(pattern)
    end = obs.index(' points out of')
    score = int(obs[start+len(pattern):end])
    return score

def test_score_detection():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
    # Murdac has some irregularities with the score, so we only test at the end
    assert manual_score(env) == score

def test_inventory():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    for act in solution[:4]:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert '(KEY)' in inv_names

def find_score():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    manual_score(env)
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        score = manual_score(env)
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

def find_move_count():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
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

def test_world_change():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    for act in solution[:20]:
        obs, _, _, _ = env.step(act)
        assert env.world_changed(),\
            "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
            .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/murdac.z5", seed=4)
    print(env.reset())
    obs, score, done, _ = env.step('look')
    # world_objs = [env.get_object(i) for i in range(175)]
    world_objs = env.get_world_objects()
    for o in world_objs:
        print(o)
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

test_murdac()
#find_move_count()
#find_score()
#viz_objs()
