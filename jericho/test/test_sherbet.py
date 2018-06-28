# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'x amelia/i/x amilia/x hat/my hat/x my hat/x fedora/show fedora to amilia/ask amilia about guide book/get book/throw glass at amilia/x boy/x branches/x woods/x branch/x elephant/x basket/i/search cushion/look through telescope/search amilia/look at amilia through telescope/look at flag through telescope/look at forest through telescope/ask amilia about smugglers/xyzzy/look at wall through telescope/look at estate through telescope/ask amilia about wall/x bird/look at bird through telescope/tell amilia about bird/ask amilia about bird/say eww/amilia/eww/snog amilia/kiss amilia/nod/yes/yawn/sleep/ask amilia about guidebook/ask amilia about guide book/give telescope to amilia/ask amilia for guide book/amilia/look at bird through telescope/x guide book/take guide book/look up bird in book/look up bird of paradise in book/chirrup/coo/x bird/look through telescope at forest/look/get feather/i/x elephant/d/x ears/pull right ear/pour sherbet on elephant/pull left ear/x painting/x faces/x lake/look/get guide/x figurine/get it/look under bed/g/x figurine/e/look up figurine in guide book/i/eat guide/xyzzy/look up xyzzy in guide book/x bed/xyzzy/look up painting in guide book/l/x bed/x painting/look behind painting/move painting/pull painting/lie on bed/x roof/x design/x design/sleep/look/out/look/e/x curtains/open curtains'

solution = walkthrough.split('/')

def test_sherbet():
    env = FrotzEnv("../roms/sherbet.z5", seed=4)
    env.reset()
    for act in solution:
        print(act, env.step(act))

def test_max_score():
    env = FrotzEnv("../roms/sherbet.z5", seed=4)
    assert env.get_max_score() == 30

def test_load_save_file():
    fname = 'sherbet.qzl'
    env = FrotzEnv("../roms/sherbet.z5", seed=4)
    env.reset()
    for act in solution[:80]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    for act in solution[80:]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/sherbet.z5", seed=4)
    env.reset()
    for act in solution[:80]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    for act in solution[80:]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    idx = obs.index('/')
    return int(obs[idx-2:idx])

def manual_moves(env, obs):
    idx = obs.index('/')
    return int(obs[idx+1:obs.index('\n',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/sherbet.z5", seed=5)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

def test_move_detection():
    env = FrotzEnv("../roms/sherbet.z5", seed=5)
    env.reset()
    for idx, act in enumerate(solution[:30]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/sherbet.z5", seed=5)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'jade figurine' in inv_names

def find_score():
    env = FrotzEnv("../roms/sherbet.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
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
    env = FrotzEnv("../roms/sherbet.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        moves = manual_moves(env, obs)
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

# def test_world_change():
#     env = FrotzEnv("../roms/sherbet.z5", seed=5)
#     env.reset()
#     for act in solution:
#         obs, _, _, _ = env.step(act)
#         assert env.world_changed(),\
#             "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
#             .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/sherbet.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/sherbet.z5", seed=5)
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

test_sherbet()
#find_moves()
#find_score()
#viz_objs()
