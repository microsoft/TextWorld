# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *

walkthrough = 'u/x marker/x branch/take it/take limb/x it/x church/x gate/x fence/e/x wall/east/x weeds/search weeds/e/se/n/x dog/dog, hello/pet dog/give stick to dog/i/give limb to dog/beat dog with limb/play fetch/attack dog with limb/throw limb/undo/throw stick/x trees/throw limb/get limb/x steeple/climb trees/n/n/nw/x graves/w/x boards/take boards/x grave/read grave/l/x graves/dig with limb/dig dirt/dig mud/e/e/se/nw/ne/se/x debris/search it/x trees/x weeds/search weeds/sw/x debris/x chain/s/windows/x windows/walk around tree/hide behind tree/pry boards/nw/x chain/put limb in chain/throw limb at chain/take chain/wave stick/x church wall/wave limb/dig/ne/x wall/verbose/verbose/x south wall/x church/n/x windows/take shingle/enter window/break window/l/sw/x windows/ne/lift limb/se/dig/sw/x window/raise limb/throw limb nw/ask dog about church/break limb/s/eat dog/growl/x rain/climb roof/bark/ne/hit dog with limb/hit dog/nw/hit dog/sw/hit dog/sw/se/n/x me/x railing/break section/break railing/touch railing/push railing/take section/x it/x ladder/look/north/x door/drop ladder/climb ladder/get ladder/lean ladder/put ladder on door/north/x portrait/x pews/take painting/north/x podium/x book/read book/take book/north/x desk/search desk/x journal/x ash/x glass/take stopper/take ash/put ash on journal/read journal/take journal/i/x shelves/x stopper/l/x weight/move bookshelf/take old book/x it/read it/x robe/take it/search it/l/wear robe/south/south/x eyes/put ladder on painting/climb ladder/north/push podium/climb podium/x painting/put ladder on podium/x eyes/stand on podium/climb ladder/up/take ladder/x archway/s/put ladder on archway/x pews/put ladder on wall/any/search pews/put ladder under painting/climb it/move painting/open it/look behind painting/x holes/look in holes/pull  painting/break painting/take painting/enter painting/enter holes/cut painting/put limb in holes/x curtain/x pulpit/reach in holes/look behind curtains/take ladder/down/take ladder/s/put ladder under trapdoor/put ladder under trap/climb ladder/full score/get rope/x rope/x door/up/climb rope/drop it. climb it/x town/x tree/oak/branch/x bell/hit bell/kick bell/ring bell/push bell/look in bell/climb branch/get branch/climb out window/stand on branch/climb tree/climb oak trees/grab branch/climb rope/open door/x door/x handle/i/hit door with limb/hit door/knock on door/climb rope/tie rope to branch/push bell/climb rope/pull branch/tie rope to door/up/push bell/down/climb rope/climb tree/branch/climb down trees/climb down branch/climb beams/look/s/d/break branch/tie robe to limb/look/tree/x frame/i/north/jump/undo/SAVE/cf1/s/jump/undo/d/x tree/x tree/branch/i/n/x beams/climb beams/x droppings/restart/yes/up/x branch/take limb/se/e/se/attack dog/ne/attack dog/nw/attack dog/sw/attack dog/se/ne/sw/n/push railing/take ladder/n/n/x podium/n/n/get ash/put ash on journal/take robe/x ashes/take book/pile/x pile/x glass/take stopper/take book/push bookshelf/take old book/l/s/verbose/x podium/take book/all/s/put ladder under trap/s/put ladder under trap/climb ladder/take ladder/uh oh/save/i/SAVE/cf1/l/tie rope to handle/pull rope/climb beams/throw stopper at bell/up/tie rope to branch/sit on bell/x mount/down/tie rope to handle/pull rope/i/look/climb down/down/take ladder/s/s/x tree/put ladder under tree/climb ladder/n/push bell/s/down/get ladder/n/n/put ladder under trap/climb ladder/north/x old man/x table/x symbols/x lantern/take lantern/clean lantern/wipe lantern with robe/x glasses/x bottles/open curtains/open curtain/x curtain/move it'
short = 'u/take limb/e/e/e/se/n/give limb to dog'

solution = walkthrough.split('/')

def test_awaken():
    env = FrotzEnv("../../TextWorld-baselines/games/awaken.z5", seed=4)
    env.reset()
    for act in solution:
        print("{} {}".format(act, env.step(act)))
        loc = env.get_player_location()
        print("Loc {}-{}".format(loc.name, loc.num))
        for i in env.get_inventory():
            print("  {}-{}".format(i.name, i.num))
        print('')

def test_max_score():
    env = FrotzEnv("../roms/awaken.z5", seed=4)
    assert env.get_max_score() == 50

def test_load_save_file():
    fname = 'awaken.qzl'
    env = FrotzEnv("../roms/awaken.z5", seed=4)
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
    env = FrotzEnv("../roms/awaken.z5", seed=4)
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

def manual_score(env, obs):
    idx = obs.index('/')
    return int(obs[idx-2:idx])

def manual_moves(env, obs):
    idx = obs.index('/')
    return int(obs[idx+1:obs.index('\n',idx)])

def test_score_detection():
    env = FrotzEnv("../roms/awaken.z5", seed=5)
    env.reset()
    for act in solution:
        obs, score, done, _ = env.step(act)
        assert manual_score(env, obs) == score

def test_move_detection():
    env = FrotzEnv("../roms/awaken.z5", seed=5)
    env.reset()
    for idx, act in enumerate(solution[:30]):
        obs, score, done, info = env.step(act)
        assert info['moves'] == manual_moves(env, obs)

def test_inventory():
    env = FrotzEnv("../roms/awaken.z5", seed=5)
    env.reset()
    for act in solution:
        env.step(act)
    inv = env.get_inventory()
    inv_names = [o.name for o in inv]
    assert 'oil lantern' in inv_names

def find_score():
    env = FrotzEnv("../roms/awaken.z5", seed=5)
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
    env = FrotzEnv("../roms/awaken.z5", seed=5)
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
#     env = FrotzEnv("../roms/awaken.z5", seed=5)
#     env.reset()
#     for act in solution:
#         obs, _, _, _ = env.step(act)
#         assert env.world_changed(),\
#             "Expected world change: Act: \"{}\" Obs: \"{}\" Diff: {}"\
#             .format(act, obs, env.get_world_diff())

def test_game_over():
    env = FrotzEnv("../roms/awaken.z5", seed=4)
    env.reset()
    for act in solution:
        env.step(act)
        assert not env.game_over()

def viz_objs():
    import pydot
    env = FrotzEnv("../roms/awaken.z5", seed=5)
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

test_awaken()
#find_moves()
#find_score()
#viz_objs()
