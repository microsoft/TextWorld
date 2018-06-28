# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = "l/l/l/l/read paper/e/search grate/search window/knock on window/w/n/x tables/note tables/ask angela about affliction/e/search ice/take hand/n/note vomit/note sink/note dryer/s/note counter/note stools/w/n/n/w/open cauldron/take foot/e/n/open dish washer/take right foot/s/s/s/take lamp/turn on lamp/n/n/n/d/open crate/u/s/s/x prep table/x shelf/take tongs/s/s/e/take eyes with tongs/w/n/n/n/x chopper/note it/x blade/open cover/turn screw/reach in chopper/open kit/wear tourniquet/take all/s/s/u/take key/read book/read killing/read culture/d/n/n/n/d/put eyes in body/put entrails in body/u/n/open dumpster/take all/s/d/put all in crate/no/u/s/s/s/s/w/search window/break window/x opener/take opener/e/n"
solution = walkthrough.split('/')

ROM_PATH="/home/matthew/Desktop/afflicted.z8"

def test_afflicted():
    env = FrotzEnv(ROM_PATH, seed=4)
    env.reset()
    for act in solution:
        print(act, env.step(act))

def test_max_score():
    env = FrotzEnv(ROM_PATH, seed=4)
    assert env.get_max_score() == 75

# def test_load_save_file():
#     fname = 'afflicted.qzl'
#     env = FrotzEnv(ROM_PATH, seed=4)
#     env.reset()
#     soln_size = len(solution)
#     for act in solution[:int(soln_size/2)]:
#         orig_obs, _, _, _ = env.step(act)
#     if os.path.exists(fname):
#         os.remove(fname)
#     env.save(fname)
#     orig_obs, _, _, _ = env.step('look')
#     for act in solution[int(soln_size/2):soln_size]:
#         new_obs, _, _, _ = env.step(act)
#     assert new_obs != orig_obs
#     env.load(fname)
#     restored, _, _, _ = env.step('look')
#     assert restored == orig_obs
#     if os.path.exists(fname):
#         os.remove(fname)

# def test_load_save_str():
#     env = FrotzEnv(ROM_PATH, seed=4)
#     env.reset()
#     soln_size = len(solution)
#     for act in solution[:int(soln_size/2)]:
#         orig_obs, _, _, _ = env.step(act)
#     save = env.save_str()
#     orig_obs, _, _, _ = env.step('look')
#     for act in solution[int(soln_size/2):soln_size]:
#         new_obs, _, _, _ = env.step(act)
#     assert new_obs != orig_obs
#     env.load_str(save)
#     restored, _, _, _ = env.step('look')
#     assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    if 'You have not yet established a sanitation rating for Nikolai\'s Bar and Grill.' in obs:
        return 0
    pattern = 'Nikolai\'s Bar and Grill has earned a sanitation rating of '
    start = obs.index(pattern)
    end = obs.index(', so far.')
    score = -int(obs[start+len(pattern):end])
    return score

# def manual_score(env, obs):
#     idx = obs.rfind(':')
#     return -int(obs[idx+1:])

# def manual_moves(env, obs):
#     idx = obs.index('/')
#     return int(obs[idx+1:obs.index('\n',idx)])

def test_score_detection():
    env = FrotzEnv(ROM_PATH, seed=5)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

# def test_move_detection():
#     env = FrotzEnv(ROM_PATH, seed=5)
#     env.reset()
#     for idx, act in enumerate(solution[:30]):
#         obs, score, done, info = env.step(act)
#         assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv(ROM_PATH, seed=5)
    env.reset()
    # for act in solution:
    #     env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'Steel key' in inv_names

def find_score():
    env = FrotzEnv(ROM_PATH, seed=5)
    env.reset()
    old_ram = env.get_ram()
    old_score = 0
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        score = manual_score(env, obs)
        print(obs, score)
        curr_ram = env.get_ram()
        diff = np.nonzero(old_ram - curr_ram)[0]
        if score != old_score:
            for j in diff:
                if not j in d:
                    d[j] = 1
                else:
                    d[j] += 1
        old_ram = curr_ram
        old_score = score
    s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
    for key, value in s:
        print("{}: {}".format(key, value/float(cnt)))

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

# def find_moves():
#     env = FrotzEnv(ROM_PATH, seed=5)
#     env.reset()
#     old_ram = env.get_ram()
#     d = {}
#     cnt = 0
#     for act in solution:
#         cnt += 1
#         obs, _, _, _ = env.step(act)
#         moves = manual_moves(env, obs)
#         curr_ram = env.get_ram()
#         for idx, v in enumerate(curr_ram):
#             if v == moves:
#                 if not idx in d:
#                     d[idx] = 1
#                 else:
#                     d[idx] += 1
#         old_ram = curr_ram
#     s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
#     for key, value in s:
#         if value/float(cnt) > .9:
#             print("{}: {}".format(key, value/float(cnt)))

# def test_world_change():
#     env = FrotzEnv(ROM_PATH, seed=5)
#     env.reset()
#     for act in solution:
#         obs, _, _, _ = env.step(act)
#         assert env.world_changed(),\
#             "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
#             .format(act, obs, env.get_world_diff())

# def test_game_over():
#     env = FrotzEnv(ROM_PATH, seed=4)
#     env.reset()
#     for act in solution:
#         env.step(act)
#         assert not env.game_over()

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

# test_afflicted()
# find_moves()
# find_score()
viz_objs()
