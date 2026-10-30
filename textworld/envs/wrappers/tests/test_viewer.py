# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import textworld

from selenium.webdriver.support.ui import WebDriverWait

from textworld.utils import make_temp_directory
from textworld.generator import compile_game
from textworld.envs.wrappers.viewer import HtmlViewer
from textworld.render import get_webdriver


def test_html_viewer(monkeypatch):
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
    probe = '<viewer-probe>literal</viewer-probe> & "quotes" \'apostrophes\' &lt;entities&gt; \u00e9'
    objective = "Objective " + probe + "\nsecond line"
    feedback = "Feedback " + probe + "\nnext line"

    game_name = "test_html_viewer_wrapper"
    with make_temp_directory(prefix=game_name) as tmpdir:
        options.path = tmpdir
        game_file = compile_game(game, options)

        env = textworld.start(game_file)
        reset = env.reset

        def reset_with_history():
            game_state = reset()
            game_state["objective"] = objective
            game_state["feedback"] = feedback
            return game_state

        monkeypatch.setattr(env, "reset", reset_with_history)
        env = HtmlViewer(env, open_automatically=False, port=8080)
        game_state = env.reset()  # Cause rendering to occur.

    driver = None
    try:
        driver = get_webdriver()
        wait = WebDriverWait(driver, 10)

        driver.get("http://127.0.0.1:{}".format(env.port))
        nodes = driver.find_elements_by_class_name("node")
        assert len(nodes) == num_nodes
        items = driver.find_elements_by_class_name("item")

        objects = [obj for obj in game.world.objects if obj.type != "I"]
        assert len(items) == len(objects)

        assert not driver.find_elements_by_tag_name("viewer-probe")
        assert driver.find_element_by_css_selector(".history .objective-text").text == objective
        initial_feedback = driver.find_element_by_css_selector(".history .feedback-text").text
        assert initial_feedback.endswith(feedback)
        assert "&nbsp;" not in initial_feedback

        command = "look " + probe + " &quot;"
        feedback = "Updated " + probe + "\nmore &quot;"
        game_state["feedback"] = feedback
        env._server.update_state(game_state, command)
        wait.until(lambda d: d.find_elements_by_css_selector(".history .command-text"))
        assert driver.find_element_by_css_selector(".history .command-text").text == "> " + command
        assert driver.find_elements_by_css_selector(".history .feedback-text")[-1].text == feedback
        assert not driver.find_elements_by_tag_name("viewer-probe")

        driver.refresh()
        wait.until(lambda d: d.find_elements_by_css_selector(".history .command-text"))
        assert driver.find_element_by_css_selector(".history .command-text").text == "> " + command

        fallback = probe + " &quot;"
        env._server.parent_conn.send(
            dict(env._server.game_state, history="", objective=fallback, command="")
        )
        wait.until(lambda d: d.find_element_by_css_selector(".history .objective-text").text == fallback)
        assert not driver.find_elements_by_tag_name("viewer-probe")
    finally:
        env.close()
        if driver is not None:
            driver.quit()
