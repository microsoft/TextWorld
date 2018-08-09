# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = "x pet/x me/x tall thing/x bookcase/x can't scratch/smell can't scratch/x couch/x table/x lamp/x tv/x armchair/i/x me/sleep/eat pet/w/pull cloth/x shiny can/x beer/x pop/read pop/x leftovers/take sandwich fixings/x cloth/close cold box/x nose/x bowl/e/wake pet/push pet/bark/bark/push pet/bite him/lick pet/push pet/bark/jump/cry/whine/pull pet/w/e/w/take bowl/e/push pet/lick pet/give bowl to pet/ask pet for food/ask pet for couch/get on couch/x cushions/sleep/take cushion/w/down/w/drop cushion/e/x wand/take wand/look behind tv/x tv/n/x dino/look under high bed/eat dino/take sock/x high bed/x low bed/turn around/turn around/turn around/sleep/look under high bed/turn around three times/search high bed/l/n/s/show sock to pet/take sock/growl/shake sock/wave sock/chew sock/smell sock/n/w/put sock in bowl/small/get sock/e/s/show sock to pet/bark/scratch/shake/roll over/play dead/take sock/shake it/hit pet with sock/throw sock at pet/shake butt/squeeze sock/put sock on tv/get on table/x table/look under table/get on pet/look under couch/x curtains/x curtain/x drapes/w/down/w/take bowl/x frame/push bowl/pull bowl/push frame/pull frame/x cupboards/open them/hot thing/x hot thing/pull cloth/verbose/x jars/x can/get can/e/show can to pet/get on couch/take wand/d/push wand/g/g/drop wand/z/z/n"

#/undo/w/bark/push pet/smell sandwich/x cold box/roll over/beg/undo/eat sandwich//undo//undo//undo//undo//undo//undo//undo/SAVE/cf1/w/undo/n/take dino/s/w/drop dino/z/z/amusing/q/restart/lick pet/lick pet/g/bark/push pet/e/w/pull cloth/get can/shake can/e/give can to pet/scratch can't scratch/push can't scratch/we could also try drinking water from the small bowl, or flushing the sock./restart/y/w/e/n/w/drink water/g/take shower/turn on tub/enter bigger bowl/flush toilet/e/s/bite hand"

solution = walkthrough.split('/')

ROM_PATH="/home/matthew/Desktop/snacktime.z8"

def test_snacktime():
    env = FrotzEnv(ROM_PATH, seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv(ROM_PATH, seed=4)
    assert env.get_max_score() == 75

# def test_load_save_file():
#     fname = 'snacktime.qzl'
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
    pattern = 'You have so far scored '
    start = obs.index(pattern)
    end = obs.index(' out of a possible')
    score = int(obs[start+len(pattern):end])
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

test_snacktime()
# find_moves()
# find_score()
# viz_objs()
