# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'look/e/x door/x glass/unlock door/w/n/get lantern/x lantern/x self/inventory/put lantern in coat/turn off lantern/unlight lantern/x table/x bar/x workers/s/look under table/get flask/put flask in coat/s/w/nw/w/x lamps/x husband/x michael/x book/ask michael about keys/ask michael about agent/save/ask michael about help/examine book/examine book/ask michael about keys/n/read sign/read register/ring bell/x librarian/ask librarian for help/s/e/se/e/e/se/x window/open window/x fence/go under fence/up/open umbrella/move cans under window/stand on can/open window/enter window/x cabinets/w/x answering machine/push play/e/look up verlac/w/x cup/x telephone/unlock door/w/w/nw/w/s/se/sw/w/nw/w/read book/say yes/michael/tell michael about keys/show keys to michael/save/e/se/e/ask michael about direction/ask michael about directions/ask michael where/ask michael about where/s/n/s/s/w/s/s/open door/s/s/n/e/e/s/sw/nw/read notice/unlock door/open door/enter door/n/s/up/n/get in bed/sleep/get up/dress/s/d/close door/x luggage/lock door/u/n/get all/s/d/lock door/up/n/undress/get in bed/save/sleep/listen/listen/listen/listen/listen/listen/listen/listen/listen/look/get up/x pants/x back pocket/get wallet from pants/open wallet/get card/look/get all/wear coat/dress/wear coat/get all/put lantern in coast/put lantern in coat/s/d/w/x table/x cupboard/open cupboard/x lining/pull lining/get journal/read journal/n/get flashlight/open cabinet/get matches/nw/turn on flashlight'
#/get broom/unlock door/d/s/search crates/remove web/clean web/get box/read clippings/get key/put key on keyring/inv/save/n/x wires/up/se/turn off flashlight/e/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/w/e/x paintings/x scene/s/get album/read album/look up wilhelm in album/look up heinrich in album/look up elijah in album/look up mordecai in album/look up eustacia in album/look up croseus in album/w/get luggage/x luggage/up/e/n/get volume/read volume/compleat manual/x bookshelf/get poe/x safe/save/turn dial to 9/turn dial to 38/turn dial to 56/x safe/look in sfae/look in safe'

#'Se/Push can against wall/Climb can/Up/West/Push play/East/Look up Verlac (2p)/West/Unlock Door/West/West/West/NW/West/Read book/Show keys to Michael (2p)/East/SE/East/South/South/East/South/SW/NW/n/w/e/s/sw/nw'
#Unlock door/North.'

solution = walkthrough.split('/')

def test_anchor():
    env = FrotzEnv("../../TextWorld-baselines/games/anchor.z8", seed=6)
    env.reset()
    for act in solution:
        loc = env.get_player_location()
        print("Act {} {} Loc {}-{}".format(act, env.step(act), loc.name, loc.num))

def test_max_score():
    env = FrotzEnv("../roms/anchor.z8", seed=6)
    assert env.get_max_score() == 100

def test_load_save_file():
    fname = 'anchor.qzl'
    description = 'This is'
    env = FrotzEnv("../roms/anchor.z8", seed=6)
    env.reset()
    for act in solution[:10]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    # orig_obs = orig_obs[orig_obs.index(description):]
    for act in solution[10:15]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    # restored = restored[restored.index(description):]
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/anchor.z8", seed=6)
    description = 'A grim'
    env.reset()
    for act in solution[:10]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    # orig_obs = orig_obs[orig_obs.index(description):]
    for act in solution[10:15]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    # restored = restored[restored.index(description):]
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    pattern = 'You have so far scored '
    start = obs.index(pattern)
    end = obs.index(' out of a possible')
    score = int(obs[start+len(pattern):end])
    return score

def manual_moves(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    a = ', in '
    idx = obs.index(a)
    return int(obs[idx+len(a):obs.index(' move',idx)])

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
    env = FrotzEnv("../roms/anchor.z8", seed=6)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

# def test_move_detection():
#     env = FrotzEnv("../roms/anchor.z8", seed=6)
#     env.reset()
#     for idx, act in enumerate(solution):
#         obs, score, done, info = env.step(act)
#         assert info['moves'] == idx + 2

def test_inventory():
    env = FrotzEnv("../roms/anchor.z8", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'flashlight' in inv_names

def find_score():
    env = FrotzEnv("../roms/anchor.z8", seed=6)
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

# def find_moves():
#     env = FrotzEnv("../roms/anchor.z8", seed=6)
#     env.reset()
#     old_ram = env.get_ram()
#     d = {}
#     cnt = 0
#     for act in solution:
#         cnt += 1
#         obs, _, _, _ = env.step(act)
#         print(obs)
#         moves = manual_moves(env, obs)
#         print('Moves',moves)
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
#         if value/float(cnt) > .8:
#             print("{}: {}".format(key, value/float(cnt)))

def find_moves():
    env = FrotzEnv("../roms/anchor.z8", seed=4)
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

def test_game_over():
    env = FrotzEnv("../roms/anchor.z8", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/anchor.z8", seed=6)
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

test_anchor()
#find_moves()
#find_score()
#viz_objs()
