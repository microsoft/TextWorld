# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld.challenges import coin_collector
from textworld.challenges import treasure_hunter

CHALLENGES = {
    'coin_collector': coin_collector.make_game_from_level,
    'treasure_hunter': treasure_hunter.make_game_from_level,
}
