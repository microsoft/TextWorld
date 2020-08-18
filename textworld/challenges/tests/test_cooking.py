# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import textworld
from textworld.challenges import cooking


def test_making_cooking_games():
    options = textworld.GameOptions()
    options.seeds = 1234

    nb_ingredients = 2

    settings = {
        "recipe": nb_ingredients,
        "take": 1,
        "open": True,
        "open": True,
        "cook": True,
        "cut": False,
        "drop": False,
        "go": 6,
        "recipe_seed": 123,
        "split": "valid"
    }

    game = cooking.make(settings, options)
    assert len(game.metadata["ingredients"]) == nb_ingredients

    # Change only the recipe.
    options = textworld.GameOptions()
    options.seeds = 1234
    settings["recipe_seed"] = 321
    game2 = cooking.make(settings, options)

    # Recipe's ingredients should be different.
    assert game.metadata["ingredients"] != game2.metadata["ingredients"]
    assert game.metadata["entities"] == game2.metadata["entities"]

    # The rest of the world should stay the same.
    POSITIONNING_FACTS = ("in", "on", "at", "west_of", "east_of", "south_of", "north_of")
    differing_facts = set(game.world.facts) - set(game2.world.facts)
    assert [pred for pred in differing_facts if pred.name in POSITIONNING_FACTS] == []

    # TODO: Check the game can be completed by following the walkthrough.
    # agent = WalkthroughAgent(commands=game.metadata["walkthrough"])
