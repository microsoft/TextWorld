# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import glob
import time
import datetime
import logging
import argparse
import importlib
import platform

from tqdm import tqdm

import textworld


log = logging.getLogger("tw-benchmark")


def evaluate(agent, game, args):
    env = textworld.start(game)
    log.debug("Using {}".format(env.__class__.__name__))
    agent.reset(env)

    start_time = time.time()
    game_state = env.reset()
    log.debug("Environment reset.\n{}\n".format(env.render(mode="text")))

    max_score = game_state.max_score
    nb_losts = 0
    highscore = 0
    score = 0
    done = False

    for step in range(1, args.nb_steps + 1):
        action = agent.act(game_state, score, done)
        game_state, score, done = env.step(action)

        msg = "{:5d}. Time: {:9.2f}\tScore: {:3d}\tMove: {:5d}\tAction: {:20s}"
        msg = msg.format(step, time.time() - start_time, game_state.score, game_state.moves, action)
        log.info(msg)
        log.debug(env.render(mode="text"))

        if done:
            highscore = max(score, highscore)

            if game_state.won:
                if highscore == max_score:
                    break  # No reason to play that game more.
            elif game_state.lost:
                nb_losts += 1
            else:
                assert True, "Games should either end with a win or a fail."

            # Replay the game in the hope of achieving a better score.
            game_state = env.reset()
            log.debug("Environment reset.\n{}\n".format(env.render(mode="text")))

    env.close()

    # Keep highest score.
    highscore = max(score, highscore)

    return step, nb_losts, highscore, max_score, time.time() - start_time


def benchmark(agent, games, args):
    game_exclusion_list = ["enter.z5", "sherlock.z5", "sherbet.z5", "theatre.z5", "balances.z5"]

    mean_score = 0
    total_time = 0.
    total_steps = 0

    nb_games = 0
    games = sorted(games)
    max_game_name = max(len(os.path.basename(game)) for game in games)
    with tqdm(total=len(games), leave=False) as pbar:
        for game in games:
            game_name = os.path.basename(game)
            pbar.set_postfix_str(game_name)
            if game_name in game_exclusion_list:
                pbar.write("{} (skip)".format(game_name))
                log.info("Excluded game: {}".format(game_name))
                pbar.update(1)
                continue  # Skip excluded games.
            try:
                nb_steps, nb_losts, final_score, max_score, seconds = evaluate(agent, game, args)
            except ValueError as e:
                pbar.write("{} (skip)".format(game_name))
                log.error(str(e))
                pbar.update(1)
                continue  # Skip not supported games.

            nb_games += 1

            norm_score = 100.0 * final_score / max_score
            assert norm_score <= 100.0
            total_time += seconds
            total_steps += nb_steps

            msg = "{}\t{:5.0f} seconds\t{:4d} losts\tScore: {:3d}/{:3d} ({:6.2f}%)"
            msg = msg.format(game_name.ljust(max_game_name), seconds, nb_losts, final_score, max_score, norm_score)
            log.info(msg)
            pbar.write(msg)
            pbar.update(1)

            mean_score += norm_score

    log.critical("Mean score (over {} games) = {:8.4f}% of total possible".format(nb_games, mean_score / nb_games))
    log.critical("Total time {:9.2f} seconds".format(total_time))
    log.critical("Avg. speed: {:8.2f} steps per second".format(total_steps / total_time))


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def setup_logging(args):
    log.setLevel(logging.DEBUG)

    fh = logging.FileHandler('tw_benchmark.log', mode='w')
    formatter = logging.Formatter("%(asctime)s: %(message)s")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    ch = TqdmLoggingHandler()
    formatter = logging.Formatter("%(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)

    ch.setLevel(logging.CRITICAL)
    if args.verbose:
        ch.setLevel(logging.INFO)

    if args.very_verbose:
        ch.setLevel(logging.DEBUG)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", metavar="game", nargs="+", required=False,
                        help="Games on which to evaluate the agent(s). By default,"
                             " use all games found in './games/'")
    parser.add_argument("--agent", default="./agent_template.py:CustomAgent",
                        help="Full qualified class name to evaluate. Default: %(default)s")
    parser.add_argument("--nb-steps", type=int, default=1000,
                        help="Maximum number of steps per game.")
    parser.add_argument("--summary_out_file", default="summary.txt",
                        help="Summary information will be written to this file.")
    parser.add_argument("--log_file", default="tw_benchmark.log",
                        help="Verbose information will be written to this file.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("-vv", "--very-verbose", action="store_true", help="Display actions taken.")
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args)
    args.verbose = args.verbose or args.very_verbose

    # Dynamically load agent class.
    path, klass = args.agent.split(":")
    spec = importlib.util.spec_from_file_location("textworld.benchmark.agents", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, klass):
        msg = "python file '{}' has no class '{}'".format(path, klass)
        raise AttributeError(msg)

    Agent = getattr(mod, klass)

    # Log some info about the machine.
    log.info('system = {}'.format(platform.system()))
    log.info('server = {}'.format(platform.uname()[1]))
    log.info('working_dir = {}'.format(os.getcwd()))
    log.info('datetime = {}'.format(datetime.datetime.now()))

    agent = Agent()
    games = args.games or glob.glob("./games/*.z?")
    benchmark(agent, games, args)


if __name__ == "__main__":
    main()
