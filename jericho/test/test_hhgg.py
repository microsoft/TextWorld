# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

solution = ['get up', 'turn on', 'take gown', 'put on gown', \
            'look in pocket', 'take pill', 'take toothbrush', 'take screwdriver',\
            'south', 'take mail', 'south', 'lie down in mud', 'wait', 'wait',\
            'wait', 'wait', 'wait', 'wait', 'wait', 's', 'w', 'drink beer',\
            'buy sandwich', 'drink beer', 'drink beer', 'exit','give sandwich to dog',\
            'n', 'kill prosser', 'wait', 'wait', 'get device', 'press green button']

def test_hhgg():
    env = FrotzEnv("../../text-agents/roms/hhgg.z3", seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    assert env.get_max_score() == 400

def test_load_save_file():
    fname = 'hhgg.qzl'
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
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
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
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
    env.step('score')
    obs, _, _, _ = env.step('')
    start = obs.index('Your score is ')
    end = obs.index(' of a possible 400')
    score = int(obs[start+len('Your score is '):end])
    return score

def test_score_detection():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env) == score

def test_move_detection():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    env.reset()
    for idx, act in enumerate(solution[:17]): # Time passes erraticly after step 18
        obs, score, done, info = env.step(act)
        assert info['moves'] == (idx + 1)

def test_self_object():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    env.reset()
    obs, score, done, _ = env.step('look')
    obs, score, done, _ = env.step('get up')
    obs, score, done, _ = env.step('turn on')
    obs, score, done, _ = env.step('take gown')
    obs, score, done, _ = env.step('put on gown')
    obs, score, done, _ = env.step('look in pocket')
    obs, score, done, _ = env.step('take pill')
    obs, score, done, _ = env.step('take toothbrush')
    obs, score, done, _ = env.step('take screwdriver')
    obs, score, done, _ = env.step('south')
    diff = env.get_world_diff()
    moved_objs = diff[0]
    self_obj_num = env.get_self().num
    assert self_obj_num in moved_objs[:][0]

def test_inventory():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    env.reset()
    obs, score, done, _ = env.step('look')
    obs, score, done, _ = env.step('get up')
    obs, score, done, _ = env.step('turn on')
    obs, score, done, _ = env.step('take gown')
    obs, score, done, _ = env.step('put on gown')
    obs, score, done, _ = env.step('look in pocket')
    obs, score, done, _ = env.step('take pill')
    obs, score, done, _ = env.step('take toothbrush')
    obs, score, done, _ = env.step('take screwdriver')
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'gown' in inv_names
    assert 'toothbrush' in inv_names
    assert 'flathead screwdriver' in inv_names

def find_move_count():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
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
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
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
    invalid_actions = ['eat gown', 'jump', 'shout', 'throw', 'spray', 'stab', 'slay', 'open', 'pierce', 'thrust', 'exorcise', 'place', 'jump', 'make', 'read', 'strangle', 'swallow', 'slide', 'wave', 'look', 'dig', 'pull', 'push', 'put', 'rub', 'fight', 'ask', 'apply', 'knock', 'block', 'kick', 'break', 'wind', 'blow', 'crack', 'blast', 'yell', 'skip', 'stare', 'hurl', 'hit', 'kill', 'engrave', 'feed', 'hatch', 'swim', 'melt', 'cross', 'insert', 'lean', 'move', 'fasten', 'play', 'drink', 'climb', 'walk', 'consume', 'kiss', 'startle', 'shout', 'cast', 'set', 'drive', 'lift', 'strike', 'speak', 'think', 'answer', 'tell', 'feel', 'turn', 'listen', 'watch', 'wash', 'purchase', 'do', 'fasten', 'drag', 'swing', 'empty', 'switch', 'slip', 'twist', 'shoot', 'slice', 'burn']
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    env.reset()
    for act in solution[:10]:
        save = env.save_str()
        for inv in invalid_actions:
            env.load_str(save)
            obs, _, _, _ = env.step(inv)
            assert not env.world_changed(),\
                "Unexpected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
                .format(inv, obs, env.get_world_diff())
        env.load_str(save)
        obs, _, _, _ = env.step(act)
        assert env.world_changed(),\
            "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
            .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()
    env.reset()
    env.step('sleep')
    assert env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/hhgg.z3", seed=4)
    print(env.reset())
    obs, score, done, _ = env.step('look')
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

test_hhgg()
#viz_objs()
