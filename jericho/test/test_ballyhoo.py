# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'S  - LIFT THUMB - S - GET POLE - N - N - N - CLIMB UP - E - E - E  -  E  -  E - E - GET BALLOON - W - W - W - W - W - W - DOWN - DOWN - GET POLE - S - S - W - GET MASK - S - W - HIDE -  WAIT - WAIT - E - N - E - N - NE - SEARCH GARBAGE - GET TICKET - PRESS BLUE DOT - SW -  S - PUT TICKET IN SLOT  -  E - S - SE - LOOK INSIDE CAGE - GET KEY WITH POLE -  UNLOCK CAGE - OPEN CAGE - ENTER CAGE - GET THE HEADPHONES AND THE BUCKET - S - NW - N - W -  W  -  S  -  UNTIE  BALLOON  -  BREATH HELIUM - SPEAK TO HARRY - S UNLOCK COMPARTMENT  -  OPEN IT - GET WHIP - W - WEAR MASK - KNOCK ON THE DOOR - GO IN  -  CLOSE  DOOR  -  LOOK IN THE ASH - GET NEWSPRINT - WAIT - LIFT WALL - CRAWL  UNDER IT - GET TRAP - WAIT - (SOMETIMES 4X) - FEEL THE ROLE -  UNSET THE TRAP - PUT THE CHEESE IN TRAP - REMOVE THE MEAT - DROP TRAP'
solution = walkthrough.split(' - ')

def test_ballyhoo():
    env = FrotzEnv("../../TextWorld-baselines/games/ballyhoo.z3", seed=6)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        if loc:
            print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    assert env.get_max_score() == 200

def test_load_save_file():
    fname = 'ballyhoo.qzl'
    description = 'This area'
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    env.reset()
    for act in solution[:5]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    orig_obs = orig_obs[orig_obs.index(description):]
    for act in solution[5:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    restored = restored[restored.index(description):]
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    description = 'This area'
    env.reset()
    for act in solution[:5]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    orig_obs = orig_obs[orig_obs.index(description):]
    for act in solution[5:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    restored = restored[restored.index(description):]
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    pattern = 'Your score is '
    start = obs.index(pattern)
    end = obs.index(' of a possible')
    score = int(obs[start+len(pattern):end])
    return score

def manual_moves(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    a = ', in '
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index(' turn',idx)])

# def manual_score(env, obs):
#     a = 'Score: '
#     print(obs)
#     idx = obs.index(a)
#     return int(obs[idx+len(a):obs.index(' Moves:',idx)])

# def manual_moves(env, obs):
#     a = 'Moves: '
#     idx = obs.index(a)
#     return int(obs[idx+len(a):obs.index('\n',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

def test_move_detection():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    env.reset()
    for idx, act in enumerate(solution):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'bucket' in inv_names

def find_score():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
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
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
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

def test_game_over():
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    env.reset()
    for act in solution:
        print(act, env.step(act))
        diff = env.get_world_diff()
        print("Diff: Obj {} SetAttr {} ClrAttr {}\n".format(diff[0], diff[1], diff[2]))

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/ballyhoo.z3", seed=6)
    print(env.reset())
    obs, score, done, _ = env.step('look')
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

test_ballyhoo()
#find_moves()
#find_score()
# test_game_over()
# viz_objs()
