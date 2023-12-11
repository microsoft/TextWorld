# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import time
import argparse
from os.path import join as pjoin

import numpy as np

import textworld.gym

import textworld
from textworld import g_rng

from textworld.generator.game import GameOptions


def generate_never_ending_game(args):
    g_rng.set_seed(args.seed)

    msg = "--max-steps {} --nb-objects {} --nb-rooms {} --quest-length {} --quest-breadth {} --seed {}"
    print(msg.format(args.max_steps, args.nb_objects, args.nb_rooms, args.quest_length, args.quest_breadth, g_rng.seed))
    print("Generating game...")

    options = GameOptions()
    options.seeds = g_rng.seed
    options.nb_rooms = args.nb_rooms
    options.nb_objects = args.nb_objects
    options.quest_length = args.quest_length
    options.quest_breadth = args.quest_breadth

    game = textworld.generator.make_game(options)
    if args.no_quest:
        game.quests = []

    game_name = "neverending"
    path = pjoin(args.output, game_name + ".ulx")
    options = textworld.GameOptions()
    options.path = path
    options.force_recompile = True
    gamefile = textworld.generator.compile_game(game, options)
    return gamefile


def benchmark(gamefile, args):
    infos = textworld.EnvInfos()
    if args.activate_state_tracking or args.mode == "random-cmd":
        infos.admissible_commands = True

    if args.compute_intermediate_reward:
        infos.intermediate_reward = True

    env = textworld.start(gamefile, infos)
    print("Using {}".format(env))

    if args.mode == "random":
        agent = textworld.agents.NaiveAgent()
    elif args.mode == "random-cmd":
        agent = textworld.agents.RandomCommandAgent(seed=args.agent_seed)
    elif args.mode == "walkthrough":
        agent = textworld.agents.WalkthroughAgent()

    agent.reset(env)
    game_state = env.reset()

    if args.verbose:
        env.render()

    reward = 0
    done = False
    nb_resets = 1
    start_time = time.time()
    for _ in range(args.max_steps):
        command = agent.act(game_state, reward, done)
        game_state, reward, done = env.step(command)

        if done:
            env.reset()
            nb_resets += 1
            done = False

        if args.verbose:
            env.render()

    duration = time.time() - start_time
    speed = args.max_steps / duration
    msg = "Done {:,} steps in {:.2f} secs ({:,.1f} steps/sec) with {} resets."
    print(msg.format(args.max_steps, duration, speed, nb_resets))
    return speed


def benchmark_gym(gamefile, args):
    infos = textworld.EnvInfos(admissible_commands=True)
    env_id = textworld.gym.register_games([gamefile] * args.batch_size, infos, args.batch_size)
    env = textworld.gym.make(env_id)
    print("Using {}".format(env.__class__.__name__))

    rng = np.random.RandomState(args.seed)

    obs, infos = env.reset()

    if args.verbose:
        print(obs[0])

    start_time = time.time()
    for _ in range(args.max_steps):
        command = rng.choice(infos["admissible_commands"][0])
        obs, _, dones, infos = env.step([command] * args.batch_size)

        if all(dones):
            env.reset()

        if args.verbose:
            print(obs[0])

    duration = time.time() - start_time
    speed = args.max_steps / duration
    print("Done {:,} steps in {:.2f} secs ({:,.1f} steps/sec)".format(args.max_steps, duration, speed))
    return speed


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game",
                        help="Path to an existing game.")
    parser.add_argument("--gym", action="store_true",
                        help="Use Gym to run the game.")
    parser.add_argument("--nb-rooms", type=int, default=20,
                        help="Nb. of rooms in the world. Default: %(default)s")
    parser.add_argument("--nb-objects", type=int, default=50,
                        help="Nb. of objects in the world. Default: %(default)s")
    parser.add_argument("--quest-length", type=int, default=5,
                        help="Minimum nb. of actions the quest requires to be completed. Default: %(default)s")
    parser.add_argument("--quest-breadth", type=int, default=1,
                        help="Control how non-linear a quest can be. Default: %(default)s")
    parser.add_argument("--max-steps", type=int, default=1000,
                        help="Stop the game after that many steps. Default: %(default)s")
    parser.add_argument("--output", default="./gen_games/",
                        help="Output folder to save generated game files.")
    parser.add_argument("--mode", default="random-cmd", choices=["random", "random-cmd", "walkthrough"])
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--no-quest", action="store_true")
    parser.add_argument("--compute_intermediate_reward", action="store_true")
    parser.add_argument("--activate_state_tracking", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--agent-seed", type=int, default=2018)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    gamefile = args.game
    if args.game is None:
        gamefile = generate_never_ending_game(args)

    speeds = []
    for _ in range(3):
        if args.gym:
            speed = benchmark_gym(gamefile, args)
        else:
            speed = benchmark(gamefile, args)
        speeds.append(speed)
        args.agent_seed = args.agent_seed + 1

    print("-----\nAverage: {:,.1f} steps/sec".format(np.mean(speeds)))
