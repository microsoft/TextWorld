# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import os
import glob
from subprocess import check_call, CalledProcessError
from os.path import join as pjoin
import textwrap

import textworld
import textworld.agents
import textworld.challenges
from textworld.utils import make_temp_directory


def test_making_a_custom_game():
    with make_temp_directory(prefix="test_tw-make") as tmpdir:
        output_folder = pjoin(tmpdir, "gen_games")
        game_file = pjoin(output_folder, "game_1234.z8")
        command = ["tw-make", "custom", "--seed", "1234", "--output", game_file, "--silent"]
        assert check_call(command) == 0

        assert os.path.isdir(output_folder)
        assert os.path.isfile(game_file)

        # Solve the game using WalkthroughAgent.
        agent = textworld.agents.WalkthroughAgent()
        textworld.play(game_file, agent=agent, silent=True)

    with make_temp_directory(prefix="test_tw-make") as tmpdir:
        output_folder = pjoin(tmpdir, "gen_games")
        game_file = pjoin(output_folder, "game_1234")  # Default extension is .z8
        command = ["tw-make", "custom", "--seed", "1234", "--output", game_file, "--silent"]
        assert check_call(command) == 0

        assert os.path.isdir(output_folder)
        assert os.path.isfile(game_file + ".z8")

        # Solve the game using WalkthroughAgent.
        agent = textworld.agents.WalkthroughAgent()
        textworld.play(game_file + ".z8", agent=agent, silent=True)

    with make_temp_directory(prefix="test_tw-make") as tmpdir:
        output_folder = pjoin(tmpdir, "gen_games", "")
        command = ["tw-make", "custom", "--seed", "1234", "--output", output_folder, "--silent"]
        assert check_call(command) == 0

        assert os.path.isdir(output_folder)
        game_file = glob.glob(pjoin(output_folder, "*.z8"))[0]

        # Solve the game using WalkthroughAgent.
        agent = textworld.agents.WalkthroughAgent()
        textworld.play(game_file, agent=agent, silent=True)

    with make_temp_directory(prefix="test_tw-make") as tmpdir:
        output_folder = pjoin(tmpdir, "gen_games")
        command = ["tw-make", "custom", "--seed", "1234", "--output", output_folder, "--silent"]
        assert check_call(command) == 0

        assert os.path.isfile(output_folder + ".z8")

        # Solve the game using WalkthroughAgent.
        agent = textworld.agents.WalkthroughAgent()
        textworld.play(output_folder + ".z8", agent=agent, silent=True)


def test_making_challenge_game():
    settings = {
        "tw-treasure_hunter": [["--level", "5"]],
        "tw-coin_collector": [["--level", "5"]],
        "tw-simple": [["--rewards", "dense", "--goal", "brief"]],
        "tw-cooking": [["--recipe", "2", "--take", "1", "--cook", "--split", "valid"],
                       ["--recipe", "2", "--take", "1", "--cook", "--drop", "--split", "valid"]],
    }
    with make_temp_directory(prefix="test_tw-challenge") as tmpdir:
        for challenge in textworld.challenges.CHALLENGES:
            for i, params in enumerate(settings[challenge]):
                output_folder = pjoin(tmpdir, "gen_games")
                game_file = pjoin(output_folder, challenge + "_{}".format(i) + ".z8")
                command = ["tw-make", challenge, "--seed", "1234", "--output", game_file, "--silent"] + params
                assert check_call(command) == 0

                assert os.path.isdir(output_folder)
                assert os.path.isfile(game_file)

                # Solve the game using WalkthroughAgent.
                agent = textworld.agents.WalkthroughAgent()
                textworld.play(game_file, agent=agent, silent=True)


def test_making_a_game_using_basic_theme():
    for i in range(10):  # Try a few different games.
        with make_temp_directory(prefix="test_tw-make") as tmpdir:
            output_folder = pjoin(tmpdir, "gen_games")
            game_file = pjoin(output_folder, "game_1234.z8")
            command = ["tw-make", "custom", "--theme", "basic", "--seed", str(i), "--output", game_file, "--silent"]
            assert check_call(command) == 0

            # Solve the game using WalkthroughAgent.
            agent = textworld.agents.WalkthroughAgent()
            textworld.play(game_file, agent=agent, silent=True)


def test_third_party():
    with make_temp_directory(prefix="test_tw-make_third_party") as tmpdir:
        challenge_py = pjoin(tmpdir, "my_challenge.py")
        with open(challenge_py, "w") as f:
            f.write(textwrap.dedent("""\
            import argparse
            from typing import Mapping, Optional

            import textworld
            from textworld.challenges import register

            from textworld import Game, GameOptions


            def build_argparser(parser=None):
                parser = parser or argparse.ArgumentParser()

                group = parser.add_argument_group('This challenge settings')
                group.add_argument("--nb-locations", required=True, type=int,
                                   help="Number of locations in the game.")

                return parser


            def make_game(settings: Mapping[str, str], options: Optional[GameOptions] = None) -> Game:
                options = options or GameOptions
                options.nb_rooms = settings["nb_locations"]
                game = textworld.generator.make_game(options)
                return game


            # Register this new challenge.
            register(name="my-challenge",
                    desc="Generate new challenge game",
                    make=make_game,
                    add_arguments=build_argparser)
            """))

        NB_LOCATIONS = 3

        output_folder = pjoin(tmpdir, "gen_games")
        game_file = pjoin(output_folder, "game_1234.z8")
        command = ["tw-make", "--third-party", challenge_py, "my-challenge", "--seed", "1234",
                   "--output", game_file, "--silent"]
        try:
            check_call(command)
        except CalledProcessError as e:
            assert e.returncode == 2  # Missing the --nb-locations argument.
        else:
            assert False, "tw-make should have failed."

        command += ["--nb-locations", str(NB_LOCATIONS)]
        assert check_call(command) == 0

        game = textworld.Game.load(game_file.replace(".z8", ".json"))
        assert len(game.world.rooms) == NB_LOCATIONS
