# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import json
import logging
import sys
sys.path.append('../')
from mcts.mcts import *

def go_fetch(env, loc, inv):
    # Teleport to the desired state and acquire inventory
    env.teleport_player(loc)
    for item in inv:
        env.teleport_obj_to_player(item)
    env.step('')


def check_actions_from_state(name, loc, inv, expected_actions, multistep_action):
    env = FrotzEnv("../roms/zork1.z5", seed=4)
    env.reset()
    go_fetch(env, loc, inv)
    obs, score, done, _ = env.step('l')
    save = env.save_str()
    game_state = State(env, obs, score, done)
    root = Node(game_state, hash2node={})
    expand(root, env)
    root_child_hashes = [hash(c) for c in root.children]

    # Check single actions
    for act in expected_actions:
        env.load_str(save)
        obs, score, done, _ = env.step(act)
        game_state = State(env, obs, score, done)
        child_hash = hash(game_state)
        assert child_hash in root_child_hashes,\
            "Missing action \"{}\". Loc: {} ({}) Inv: {} FoundActs: {}"\
            .format(act, loc, name, inv, root.actions)

    # Check multistep actions
    env.load_str(save)
    multistep = []
    for act in multistep_action:
        obs, score, done, _ = env.step(act)
        diff = env.get_world_diff()
        print(act, obs, diff)
        game_state = State(env, obs, score, done)
        multistep.append((act, game_state, diff))

    node = root
    for act, state, diff in multistep:
        child_hash = hash(state)
        assert child_hash in [hash(c) for c in node.children],\
            "Missing action \"{}\". Loc: {} ({}) Inv: {} MultistepActs: {} Discovered: {}"\
            .format(act, loc, name, inv, multistep_action, node.actions)
        node = node.hash2node[child_hash]
        expand(node, env)


def test_expand():
    while logging.root.handlers:
        logging.root.removeHandler(logging.root.handlers[0])
    logging.basicConfig(format='%(message)s', filename='test_expand.log', level=logging.DEBUG)

    data = json.load(open('zork1_locations.json'))
    for l in data["locations"]:
        name = l['name']
        if name == "sandy cave" or name == "grating room" or name == 'maintenance room' or name == 'entrance to hades':
            print("Skipping {} because of difficult world state change detection.".format(name))
            continue
        check_actions_from_state(l["name"], l["location"], l["inventory"],
                                 l["actions"], l["multistep_action"])

test_expand()
