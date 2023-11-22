# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld

from textworld.utils import make_temp_directory
from textworld.generator import compile_game
from textworld.envs.wrappers.viewer import HtmlViewer
from textworld.render import get_webdriver


def test_html_viewer():
    # Integration test for visualization service
    num_nodes = 3
    num_items = 10
    options = textworld.GameOptions()
    options.seeds = 1234
    options.nb_rooms = num_nodes
    options.nb_objects = num_items
    options.quest_length = 3
    options.grammar.theme = "house"
    options.grammar.include_adj = True
    game = textworld.generator.make_game(options)

    game_name = "test_html_viewer_wrapper"
    with make_temp_directory(prefix=game_name) as tmpdir:
        options.path = tmpdir
        game_file = compile_game(game, options)

        env = textworld.start(game_file)
        env = HtmlViewer(env, open_automatically=False, port=8080)
        env.reset()  # Cause rendering to occur.

    # options.binary_location = "/bin/chromium"
    driver = get_webdriver()

    driver.get("http://127.0.0.1:{}".format(env.port))
    nodes = driver.find_elements_by_class_name("node")
    assert len(nodes) == num_nodes
    items = driver.find_elements_by_class_name("item")

    objects = [obj for obj in game.world.objects if obj.type != "I"]
    assert len(items) == len(objects)

    env.close()
    driver.close()
