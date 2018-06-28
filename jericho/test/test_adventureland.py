# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'Go east/Go north/Get axe/Go down/Get ox/Bunyon/Swim/Go west/Go west/'\
'Get axe/Get ox/Get fruit/Go east/Climb tree/Get keys/go down/Cut tree/'\
'drop axe/get mud/go stump/drop mud/drop ox/drop fruit/go down/get rubies/'\
'up/drop rubies/get lamp'
solution = walkthrough.split('/')

def test_adventureland():
    env = FrotzEnv("../../TextWorld-baselines/games/adventureland.z5", seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    assert env.get_max_score() == 100

def test_victory():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
    for act in solution[:-1]:
        obs, _, done, _ = env.step(act)
        assert not env.victory()
    env.step(solution[-1])
    # assert env.victory()

def test_load_save_file():
    fname = 'adventureland.qzl'
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
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
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
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

def manual_score(env):
    obs, _, _, _ = env.step('score')
    a = 'You have so far scored '
    start = obs.index(a)
    end = obs.index(' out of a possible ')
    score = int(obs[start+len(a):end])
    return score

def test_score_detection():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env) == score

def test_move_detection():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
    for idx, act in enumerate(solution[:17]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == (idx + 2)

def test_inventory():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'old fashioned lamp' in inv_names

def find_move_count():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
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

def find_score():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
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
        print("{}: {}".format(key, value/float(cnt)))

def test_world_change():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
    for act in solution[:10]:
        obs, _, _, _ = env.step(act)
        assert env.world_changed(),\
            "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
            .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    env.reset()
    for act in solution[:-1]:
        env.step(act)
        assert not env.game_over()
    # TODO: How to get game over?

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/adventureland.z5", seed=4)
    print(env.reset())
    obs, score, done, _ = env.step('look')
    world_objs = env.get_world_objects()
    # world_objs = [env.get_object(o) for o in range(110)]
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

test_adventureland()
#viz_objs()
