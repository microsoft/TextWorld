# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'NW/D/get all/examine panel/turn on switch/examine barrels/get popcorn/again/again/again/U/SE/S/N/examine thug/z/z/z/z/N/drop all but pager/NW/drop pager/N/get all/W/W/S/W/push piano east/push piano south/climb up piano/open trapdoor/U/get all/N/turn handle/N/get lens/S/S/D/N/N/E/E/N/move carpet/get all/examine body/read book/N/get all/N/open bin/get page/ticket from bin/SW/S/S/S/SE/drop all but lens/U/open door/E/S/open curtains/NE/W/D/put lens in spotlight/get lens/ticket/U/E/N/push chandelier/drop ticket/E/E/U/score'

solution = walkthrough.split('/')

def test_theatre():
    env = FrotzEnv("../../TextWorld-baselines/games/theatre.z5", seed=4)
    env.reset()
    for act in solution:
        print(act, env.step(act))

def test_max_score():
    env = FrotzEnv("../roms/theatre.z5", seed=4)
    assert env.get_max_score() == 50

def test_load_save_file():
    fname = 'theatre.qzl'
    env = FrotzEnv("../roms/theatre.z5", seed=4)
    env.reset()
    soln_size = len(solution)
    for act in solution[:int(soln_size/2)]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    for act in solution[int(soln_size/2):soln_size]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/theatre.z5", seed=4)
    env.reset()
    soln_size = len(solution)
    for act in solution[:int(soln_size/2)]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    for act in solution[int(soln_size/2):soln_size]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def text2int(textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current

def manual_score(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    pattern = 'You have so far scored '
    start = obs.index(pattern)
    end = obs.index(' out of a possible ')
    textnum = obs[start+len(pattern):end]
    return text2int(textnum.replace('-',' '))

def manual_moves(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    a = 'fifty in '
    idx = obs.index(a)
    textnum = obs[idx+len(a):obs.index('turns',idx)]
    return text2int(textnum.replace('-',' '))

def test_score_detection():
    env = FrotzEnv("../roms/theatre.z5", seed=5)
    env.reset()
    swap = 35
    for act in solution[:swap]:
        obs, _, _, _ = env.step(act)
    for act in solution[swap:]:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

def test_move_detection():
    env = FrotzEnv("../roms/theatre.z5", seed=5)
    env.reset()
    swap = 35
    for act in solution[:swap]:
        obs, _, _, _ = env.step(act)
    for idx, act in enumerate(solution[swap:]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/theatre.z5", seed=5)
    env.reset()
    for act in solution[:10]:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'loose page' in inv_names

def find_score():
    env = FrotzEnv("../roms/theatre.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    swap = 35
    for act in solution[:swap]:
        obs, _, _, _ = env.step(act)
    for act in solution[swap:]:
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
    env = FrotzEnv("../roms/theatre.z5", seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    swap = 35
    for act in solution[:swap]:
        obs, _, _, _ = env.step(act)
    for act in solution[swap:]:
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
#     env = FrotzEnv("../roms/theatre.z5", seed=5)
#     env.reset()
#     for act in solution:
#         obs, _, _, _ = env.step(act)
#         assert env.world_changed(),\
#             "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
#             .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/theatre.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/theatre.z5", seed=5)
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

test_theatre()
#find_moves()
#find_score()
#viz_objs()
