# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld


from textworld import g_rng
from textworld.utils import make_temp_directory, get_webdriver
from textworld.generator import compile_game
from textworld.envs.wrappers import HtmlViewer, GlulxLogger


def test_html_viewer():
    # Integration test for visualization service
    num_nodes = 3
    num_items = 10
    g_rng.set_seed(1234)
    grammar_flags = {"theme": "house", "include_adj": True}
    game = textworld.generator.make_game(world_size=num_nodes, nb_objects=num_items, quest_length=3, grammar_flags=grammar_flags)

    game_name = "test_html_viewer_wrapper"
    with make_temp_directory(prefix=game_name) as tmpdir:
        game_file = compile_game(game, game_name, games_folder=tmpdir)

        env = textworld.start(game_file)
        env = HtmlViewer(env, open_automatically=False, port=8080)
        env.reset()  # Cause rendering to occur.

    # options.binary_location = "/bin/chromium"
    driver = get_webdriver()

    driver.get("http://127.0.0.1:8080")
    nodes = driver.find_elements_by_class_name("node")
    assert len(nodes) == num_nodes
    items = driver.find_elements_by_class_name("item")
    item_text = driver.find_elements_by_class_name('item-text')

    # TextWorld generates 14 for some reason.
    assert len(items) == num_items + 4

    tracking = env.get('tracking')

    assert len(tracking['path']) == 1

    game_state, score, done = env.step('go south')

    updated_tracking = env.get('tracking')

    print(updated_tracking)
    assert updated_tracking['entrance_count']['upsettingly hot scullery']['south'] == 1

    assert len(updated_tracking['path']) == 2

    assert updated_tracking['path'][-1] == 'upsettingly hot scullery'

    game_state, score, done = env.step('take soft coconut')

    updated_tracking_new = env.get('tracking')

    assert updated_tracking_new['highlighted']['items']['soft coconut'] == 1

    assert updated_tracking_new['room_step_count']['upsettingly hot scullery'] == 2


    env.close()
    driver.close()
