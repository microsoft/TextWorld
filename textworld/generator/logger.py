# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import pickle
import textwrap
from collections import defaultdict

__all__ = ["GameLogger"]


def zero():
    return 0


def empty_list():
    return []


def update_bincount(arr, count):
    """ Update bincount in-place. """
    if count >= len(arr):
        extend_size = count - len(arr) + 1
        arr += [0] * extend_size

    arr[count] += 1


def merge_bincout(arr1, arr2):
    arr = [0] * max(len(arr1), len(arr2))
    for i, v in enumerate(arr1):
        arr[i] += v

    for i, v in enumerate(arr2):
        arr[i] += v

    return arr


class GameLogger:
    def __init__(self, group_actions=True):
        self.group_actions = group_actions

        # Stats
        self.n_games = 0
        self.dist_obj_type = defaultdict(zero)
        self.dist_obj_type_count = defaultdict(empty_list)
        self.dist_cmd_type = defaultdict(zero)
        self.dist_final_cmd_type = defaultdict(zero)
        self.dist_quest_count = []
        self.dist_quest_length_count = []
        self.dist_obj_count = []
        self.dist_inventory_size = []
        self.quests = set()
        self.objects = set()

        # TODO:
        # Get statistic for:
        #  - Avg. description length
        #  - Avg. number of container/supporters
        #  - Avg. number of items in container/on supporters
        #  - Avg. number of free exits per world
        #  - Avg. number of doors per world
        #  - Avg. number of contiendoor per world
        #  - Distribution of the commands type
        #  - Distribution of the objects names
        #  - Number of already seen environments
        #  - Number of commands per game

    def collect(self, game):
        self.n_games += 1

        # Collect distribution of nb. of commands.
        update_bincount(self.dist_quest_count, len(game.quests))

        # Collect distribution of commands leading to winning events.
        for quest in game.quests:
            self.quests.add(quest.desc)
            for event in quest.win_events:
                actions = event.actions
                update_bincount(self.dist_quest_length_count, len(actions))

                for action in actions:
                    action_name = action.name
                    if self.group_actions:
                        action_name = action_name.split("-")[0].split("/")[0]

                    self.dist_cmd_type[action_name] += 1

                self.dist_final_cmd_type[action_name] += 1

        # Collect distribution of object's types.
        dist_obj_type = defaultdict(lambda: 0)
        interactable_objects = game.world.objects
        inventory = game.world.get_objects_in_inventory()

        for obj in interactable_objects:
            self.objects.add(game.infos[obj.id].name)
            dist_obj_type[obj.type] += 1

        nb_objects = 0
        for type_ in game.kb.types:
            if type_ in ["I", "P", "t", "r"]:
                continue

            count = dist_obj_type[type_]
            nb_objects += count
            self.dist_obj_type[type_] += count
            update_bincount(self.dist_obj_type_count[type_], count)

        update_bincount(self.dist_obj_count, nb_objects)
        update_bincount(self.dist_inventory_size, len(inventory))

    def display_stats(self):
        print(self.stats())

    def stats(self):
        txt = textwrap.dedent("""\
        Nb. games: {n_games}

        Quests count: {dist_quest_count} ({unique_quest_count} unique)

        Quest length count: {dist_quest_length_count}

        Objects: {dist_obj_count} ({unique_obj_count} unique)

        Inventory: {dist_inventory_size}

        Objects types overall:
          {dist_obj_type}

        Objects types per game:
          {dist_obj_type_count}

        Commands types [{nb_cmd_type}]:
          {dist_cmd_type}

        Final command types [{nb_final_cmd_type}]:
          {dist_final_cmd_type}

        """)

        def bincount_str(bincount):
            text = []
            for i, c in enumerate(bincount):
                text.append(str(c))
                if (i+1) % 5 == 0 and (i+1) < len(bincount):
                    text.append("|")

            return " ".join(text)

        def frequencies_str(freqs):
            if len(freqs) == 0:
                return ""

            text = []
            labels_max_len = max(map(len, freqs.keys()))
            total = float(sum(freqs.values()))
            for k in sorted(freqs.keys()):
                text += ["{}: {:5.1%}".format(k.rjust(labels_max_len),
                                              freqs[k] / total)]

            return "\n  ".join(text)

        dist_quest_count = bincount_str(self.dist_quest_count)
        dist_quest_length_count = bincount_str(self.dist_quest_length_count)
        dist_inventory_size = bincount_str(self.dist_inventory_size)
        dist_cmd_type = frequencies_str(self.dist_cmd_type)
        dist_final_cmd_type = frequencies_str(self.dist_final_cmd_type)

        dist_obj_count = bincount_str(self.dist_obj_count)
        dist_obj_type = "  ".join("{}:{}".format(k, self.dist_obj_type[k])
                                  for k in sorted(self.dist_obj_type.keys()))
        dist_obj_type_count = "\n  ".join(type_ + ": " + bincount_str(self.dist_obj_type_count[type_])
                                          for type_ in sorted(self.dist_obj_type_count.keys()))
        txt = txt.format(n_games=self.n_games,
                         dist_quest_count=dist_quest_count,
                         unique_quest_count=len(self.quests),
                         dist_quest_length_count=dist_quest_length_count,
                         dist_cmd_type=dist_cmd_type,
                         dist_final_cmd_type=dist_final_cmd_type,
                         dist_obj_count=dist_obj_count,
                         unique_obj_count=len(self.objects),
                         dist_obj_type=dist_obj_type,
                         dist_obj_type_count=dist_obj_type_count,
                         dist_inventory_size=dist_inventory_size,
                         nb_cmd_type=len(self.dist_cmd_type),
                         nb_final_cmd_type=len(self.dist_final_cmd_type))
        return txt

    def aggregate(self, other):
        assert self.group_actions == other.group_actions

        self.n_games += other.n_games
        for k, v in other.dist_obj_type.items():
            self.dist_obj_type[k] += v

        for k, v in other.dist_obj_type_count.items():
            self.dist_obj_type_count[k] = merge_bincout(self.dist_obj_type_count[k], v)

        for k, v in other.dist_cmd_type.items():
            self.dist_cmd_type[k] += v

        for k, v in other.dist_final_cmd_type.items():
            self.dist_final_cmd_type[k] += v

        self.dist_quest_count = merge_bincout(self.dist_quest_count, other.dist_quest_count)
        self.dist_quest_length_count = merge_bincout(self.dist_quest_length_count, other.dist_quest_length_count)
        self.dist_obj_count = merge_bincout(self.dist_obj_count, other.dist_obj_count)
        self.dist_inventory_size = merge_bincout(self.dist_inventory_size, other.dist_inventory_size)
        self.quests |= other.quests
        self.objects |= other.objects

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f, protocol=2)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
