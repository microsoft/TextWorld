# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


##!/usr/bin/env python
import numpy as np
import argparse
import itertools
import warnings

import textworld
import textworld.agents


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-size", type=int, default=5,
                        help="Nb. of rooms in the world.")
    parser.add_argument("--nb-objects", type=int, default=10,
                        help="Nb. of objects in the world.")
    parser.add_argument("--quest-length", type=int, default=5,
                        help="Minimum nb. of actions the quest requires to be completed.")
    parser.add_argument("--quest-breadth", type=int, default=3, metavar="BREADTH",
                        help="Control how non-linear a quest can be.")
    parser.add_argument("--output", default="./gen_games/",
                        help="Output folder to save generated game files.")
    parser.add_argument("--mode", default="human",
                        choices=["random", "random-cmd", "human", "walkthrough"])
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--nb-games", type=int, default=0)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--vizu", type=int, default=-1,
                        help="Port at which to start visualization")
    parser.add_argument("--hints", action="store_true")
    parser.add_argument("--backend", help="[Advanced] Use a specific backend.")

    cfg_parser = parser.add_argument_group('Grammar settings')
    cfg_parser.add_argument("--theme", default="house",
                            help="Theme to use for generating the text. Default: %(default)s")
    cfg_parser.add_argument("--include-adj", action="store_true",
                            help="Turn on adjectives.")
    cfg_parser.add_argument("--blend-descriptions", action="store_true",
                            help="Blend descriptions across consecutive sentences.")
    cfg_parser.add_argument("--ambiguous-instructions", action="store_true",
                            help="Refer to an object using its type (e.g. red container vs. red chest).")
    cfg_parser.add_argument("--only-last-action", action="store_true",
                            help="Intruction only describes the last action of quest.")
    cfg_parser.add_argument("--blend-instructions", action="store_true",
                            help="Blend instructions across consecutive actions.")

    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-vv", "--very-verbose", action="store_true",
                        help="Print warnings and debug information.")
    return parser.parse_args()


def make_agent(args):
    if args.mode == "random":
        agent = textworld.agents.NaiveAgent()
    elif args.mode == "random-cmd":
        agent = textworld.agents.RandomCommandAgent()
    elif args.mode == "human":
        agent = textworld.agents.HumanAgent(autocompletion=args.hints, walkthrough=args.hints)
    elif args.mode == 'walkthrough':
        agent = textworld.agents.WalkthroughAgent()
    else:
        raise ValueError("Unknown agent: {}".format(args.mode))

    return agent


def main():
    args = parse_args()
    if args.very_verbose:
        args.verbose = args.very_verbose
        warnings.simplefilter("default", textworld.TextworldGenerationWarning)

    if args.seed is None:
        args.seed = np.random.randint(65635)

    grammar_flags = {
        "theme": args.theme,
        "include_adj": args.include_adj,
        "only_last_action": args.only_last_action,
        "blend_instructions": args.blend_instructions,
        "blend_descriptions": args.blend_descriptions,
        "ambiguous_instructions": args.ambiguous_instructions
    }

    print("Random seed: {}".format(args.seed))
    rng = np.random.RandomState(args.seed)

    agent = make_agent(args)

    reward_history = []
    for i in range(args.nb_games) if args.nb_games > 0 else itertools.count():
        # Get a game seed to make everything reproducible.
        game_seed = rng.randint(65635)
        game_file, game = textworld.make(args.world_size, args.nb_objects, args.quest_length, args.quest_breadth, grammar_flags,
                                         seed=game_seed, games_dir=args.output)

        print("Starting game {}".format(game_file))
        env = textworld.start(game_file)
        agent.reset(env)

        if args.vizu >= 0:
            from textworld.envs.wrappers import HtmlViewer
            env = HtmlViewer(env, port=args.vizu)

        game_state = env.reset()
        if args.mode == "human" or args.verbose:
            env.render()

        reward = 0
        done = False

        for t in range(args.max_steps) if args.max_steps > 0 else itertools.count():
            command = agent.act(game_state, reward, done)
            game_state, reward, done = env.step(command)

            if args.mode == "human" or args.verbose:
                env.render()

            if done:
                break

        env.close()
        print("Done after {} steps. Score {}/{}.".format(game_state.nb_moves, game_state.score, game_state.max_score))

        reward_history.append(reward)
        if args.nb_games == 0:  # Interactive mode.
            input("Press enter to generate a new game.")


if __name__ == "__main__":
    main()
