# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from jericho import *
import re

walkthrough = 'd/swallow defeat/se/x stranger/sit on chair/insult joe/Yes/talk to joe/l/stand/w/nw/undo/talk to bouncer/x thermostat/set thermostat to warm/x bouncer/insult bouncer/hit bouncer/w/x plant/x vincent/talk to vincent/insult vincent/n/x arcade/insult vincent/gus/insult vincent/bouncer/insult vincent/joe/map/n/x barkeep/x dubious/insult sleaze/buy drink/hit him/read poster/talk to guy/read menu/n/x britney/talk to britney/insult guard/i/talk to guard/x jacket/x street clothes/insult britney/e/se/x norbert/insult norbert/talk to norbert/w/arcade/insult vincent/norbert/map/entrance/set thermostat to warm/ne/x ralph/talk to ralph/x satchel/insult ralph/open satchel/x jukebox/look under jukebox/x knob/turn knob to high/listen/arcade/search machines/hall of fame/i/x coins/put coin in jukebox/press ass/open satchel/put coin in jukebox/press jazz/z/n/x posse/x sweater/x tag/take tag/take sweater/remove jacket/wear sweater/wear jacket/floor/look under table/take gum/talk to norbert/e/x portraits/dark corner/talk to joe/go to bar/talk to guy/talk to guy/point at vodka/x vodka/e/w/take vodka/VIP/give vodka to guard/bar/point at cola/e/w/take cola/VIP/give cola to guard/talk to britney/g/talk to britney/s/arcade/bar/give vodka to bartender/point at vodka/take vodka/vip/give drink to britney/drop drink/look under sofa/x pass/bar/give pass to sleaze/n/talk to britney/talk to britney/search guard/tase sleaze/talk to britney/bar/point at vodka/take vodka/point at coke/take coke/pour vodka into coke/n/give cola to britney/talk to britney/floor/norbert/talk to norbert/hangout/look under loudspeaker/hall of fame/turn knob to high/hangout/hall of fame/put coin in jukebox/press techno/hangout/take lens/stage/z/dark corner/put sweater on table/look at tag through lens/stage/z/Norbert/Norbert/give lens to norbert/hangout/x gus/bar/arcade/insult vincent/sleaze/bar/arcade/insult vincent/sleaze/bar/take card/floor/scrape gum with card/hall of fame/put gum on ass button/push ass/open satchel/x books/x wallet/open wallet/stage/z/z'

solution = walkthrough.split('/')

ROM_PATH="/home/matthew/workspace/TextWorld-baselines/games/yomomma.z8"

def test_yomama():
    env = FrotzEnv(ROM_PATH, seed=4)
    env.reset()
    for act in solution:
        print(act, env.step(act))

# def find_moves():
#     env = FrotzEnv(ROM_PATH, seed=4)
#     env.reset()
#     old_ram = env.get_ram()
#     d = {}
#     cnt = 0
#     for act in solution:
#         cnt += 1
#         obs, _, _, _ = env.step(act)
#         print(obs)
#         curr_ram = env.get_ram()
#         diff = np.nonzero(old_ram - curr_ram)[0]
#         for j in diff:
#             if not j in d:
#                 d[j] = 1
#             else:
#                 d[j] += 1
#         old_ram = curr_ram
#     s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
#     for key, value in s:
#         print("{}: {}".format(key, value/float(cnt)))

def manual_score(env, obs):
    result = re.search("[0-9]+", obs)
    return int(result.group(0))

def manual_moves(env, obs):
    idx = obs.index('/')
    print(idx)
    return int(obs[idx+1:])

# def manual_moves(env, obs):
#     result = re.search("\([0-9]+", obs)
#     if not result:
#         print("OBS: ", obs)
#     return int(result.group(0)[1:])

def find_moves():
    env = FrotzEnv(ROM_PATH, seed=5)
    env.reset()
    old_ram = env.get_ram()
    d = {}
    cnt = 0
    for act in solution:
        cnt += 1
        obs, _, _, _ = env.step(act)
        print(obs)
        if 'YES' in obs:
            moves -= 1
            continue
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

test_yomama()
#find_moves()
#find_score()
#viz_objs()
