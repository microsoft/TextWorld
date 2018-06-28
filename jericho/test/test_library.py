# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'W/E/Give card to Alan/W/N/Look under stairs/U/S/Search shelves/Unlock door with key/Open door/S/Get book/N/Close door/Lock door with key/E/Ask technician about security gates/X printouts/W/N/D/S/Give encyclopedia to Marion/E/Give key to Alan/Give novel to Alan'
# Add final action 'E' to win the game
solution = walkthrough.split('/')

def test_library():
    env = FrotzEnv("../../TextWorld-baselines/games/library.z5", seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/library.z5", seed=4)
    assert env.get_max_score() == 30

def test_load_save_file():
    fname = 'library.qzl'
    env = FrotzEnv("../roms/library.z5", seed=4)
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
    env = FrotzEnv("../roms/library.z5", seed=4)
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
    pattern = 'You have so far scored '
    start = obs.index(pattern)
    end = obs.index(' out of a possible ')
    score = int(obs[start+len(pattern):end])
    return score

def manual_moves(env):
    obs, _, _, _ = env.step('score')
    print(obs)
    a = '30, in '
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index('turn',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/library.z5", seed=5)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env) == score

def test_move_detection():
    env = FrotzEnv("../roms/library.z5", seed=5)
    env.reset()
    for idx, act in enumerate(solution[:30]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(env)

def test_inventory():
    env = FrotzEnv("../roms/library.z5", seed=5)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'ID card' in inv_names

def find_score():
    env = FrotzEnv("../roms/library.z5", seed=5)
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
        if value/float(cnt) > .9:
            print("{}: {}".format(key, value/float(cnt)))

def find_moves():
    env = FrotzEnv("../roms/library.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        moves = manual_moves(env)
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
        if value/float(cnt) > .9:
            print("{}: {}".format(key, value/float(cnt)))

def test_world_change():
    env = FrotzEnv("../roms/library.z5", seed=5)
    env.reset()
    for act in solution:
        obs, _, _, _ = env.step(act)
        assert env.world_changed(),\
            "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
            .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/library.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/library.z5", seed=5)
    print(env.reset())
    obs, score, done, _ = env.step('look')
    # world_objs = [env.get_object(i) for i in range(175)]
    world_objs = env.get_world_objects()
    for o in enumerate(world_objs):
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

test_library()
#find_moves()
#find_score()
#viz_objs()
