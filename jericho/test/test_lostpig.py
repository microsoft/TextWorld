# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'x me/inventory/x farm/x forest/look for pig/listen/ne/x stairs/x metal thing/take tube/take torch/look inside tube/blow in tube/x crack/e/x pig/follow pig/catch pig/x fountain/x bowl/x coin/x curtain/x man/n/x west mural/x east mural/x statue/x hat/take hat/wear hat/s/sw/x box/put coin in slot/pull lever/x brick/take brick/smell brick/taste brick/eat brick/x dent/hit box/take coin/put coin in slot/pull level/hit box/take all from basket/put coin in slot/take all from basket/take chair/e/listen/shout/greet gnome/look under bed/open trunk/take ball/show torch to gnome/ask gnome about fire/show brick to gnome/ask gnome about mother/e/x shelf/drop chair/stand on chair/take book/down/open chest/take pole/w/SHOW POLE TO GNOME/ASK GNOME ABOUT COLOR MAGNET/SHOW BOOK TO GNOME/GIVE BOOK TO GNOME/EAST/ASK GNOME ABOUT PAGE/EAST/NORTHWEST/EAST/X RIVER/X THING/TAKE THING/CROSS RIVER/TOUCH THING WITH POLE/X KEY/TAKE WATER/FILL HAT WITH WATER/WEST/SOUTHEAST/UNLOCK CHEST/OPEN IT/POUR WATER ON POWDER/LIGHT TORCH WITH FIRE/NORTHWEST/WEST/X CRACK/TAKE PAPER/TAKE PAPER WITH POLE/BURN POLE WITH TORCH/TAKE PAPER WITH POLE/EAST/SOUTHWEST/EAST/GIVE PAPER TO GNOME/WAIT/GO TO PIG'


solution = walkthrough.split('/')

def test_lostpig():
    env = FrotzEnv("../../TextWorld-baselines/games/lostpig.z8", seed=6)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    assert env.get_max_score() == 7

def test_load_save_file():
    fname = 'lostpig.qzl'
    description = 'This is'
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    env.reset()
    for act in solution[:5]:
        orig_obs, _, _, _ = env.step(act)
    if os.path.exists(fname):
        os.remove(fname)
    env.save(fname)
    orig_obs, _, _, _ = env.step('look')
    # orig_obs = orig_obs[orig_obs.index(description):]
    for act in solution[5:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load(fname)
    restored, _, _, _ = env.step('look')
    # restored = restored[restored.index(description):]
    assert restored == orig_obs
    if os.path.exists(fname):
        os.remove(fname)

def test_load_save_str():
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    description = 'This is'
    env.reset()
    for act in solution[:5]:
        orig_obs, _, _, _ = env.step(act)
    save = env.save_str()
    orig_obs, _, _, _ = env.step('look')
    # orig_obs = orig_obs[orig_obs.index(description):]
    for act in solution[5:10]:
        new_obs, _, _, _ = env.step(act)
    assert new_obs != orig_obs
    env.load_str(save)
    restored, _, _, _ = env.step('look')
    # restored = restored[restored.index(description):]
    assert restored == orig_obs, "Orig: {}, Restored {}".format(orig_obs, restored)

def manual_score(env, obs):
    obs, _, _, _ = env.step('score')
    print(obs)
    pattern = 'Grunk have '
    start = obs.index(pattern)
    end = obs.index(' out of')
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
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

# def test_move_detection():
#     env = FrotzEnv("../roms/lostpig.z8", seed=6)
#     env.reset()
#     for idx, act in enumerate(solution):
#         obs, score, done, info = env.step(act)
#         assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'pole' in inv_names

def find_score():
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
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
#     env = FrotzEnv("../roms/lostpig.z8", seed=6)
#     env.reset()
#     old_ram = env.get_ram()
#     d = {}
#     cnt = 0
#     for act in solution:
#         cnt += 1
#         obs, _, _, _ = env.step(act)
#         print(obs)
#         moves = cnt +1 #manual_moves(env, obs)
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
    env = FrotzEnv("../roms/lostpig.z8", seed=4)
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
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
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

def test_world_change():
    env = FrotzEnv("../roms/lostpig.z8", seed=6)
    env.reset()
    for act in solution:
        print(act, env.step(act))
        diff = env.get_world_diff()
        print("Diff: Obj {} SetAttr {} ClrAttr {}\n\n".format(diff[0], diff[1], diff[2]))

test_lostpig()
#find_moves()
#find_score()
#viz_objs()
#test_world_change()
