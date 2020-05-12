import os
import argparse
from os.path import join as pjoin
from typing import Mapping, Optional

from textworld import GameMaker
from textworld.challenges import register
from textworld.generator.data import KnowledgeBase
from textworld.generator.game import GameOptions, QuestProgression, GameProgression


PATH = os.path.dirname(__file__)


def build_argparser(parser=None):
    parser = parser or argparse.ArgumentParser()

    group = parser.add_argument_group('Test_content game settings')
    group.add_argument("--level", required=True, choices=["test"],
                       help="This is a test file; thus, the level is set to test.")
    general_group = argparse.ArgumentParser(add_help=False)
    general_group.add_argument("--third-party", metavar="PATH",
                               help="Load third-party module. Useful to register new custom challenges on-the-fly.")
    return parser


class TestContentCheck:
    @classmethod
    def setUpClass(cls, options):
        #
        # kb = KnowledgeBase.load(target_dir=pjoin(os.path.dirname(__file__), 'textworld_data'))
        # options = options or GameOptions()
        # options.grammar.theme = 'spaceship'
        # options.kb = kb

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #                                    Create the Game Environment
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        M = GameMaker(options=options)

        # ===== Test Room Design =======================================================================================
        test_room = M.new_room("Test Room")

        table = M.new(type='s', name='Table')
        test_room.add(table)

        laptop = M.new(type='cpu', name='laptop')
        table.add(laptop)
        M.add_fact('unread/e', laptop)

        red_box = M.new(type='c', name="Red box")
        table.add(red_box)
        M.add_fact("closed", red_box)

        blue_box = M.new(type='c', name="Blue box")
        table.add(blue_box)
        M.add_fact("closed", blue_box)

        # ===== Player and Inventory Design ============================================================================
        M.set_player(test_room)

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #                                    Create the Quests (of the game)
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # 1. Defining two events, one EventCondition and one EventAction, and then test the EventOr and EventAnd
        #    performance within two different quests.
        # commands = ['open Red box', 'open Blue box', 'take laptop from Table']
        commands = ['open Red box', 'open Blue box']
        cls.eventA = M.new_event_using_commands(commands, event_style='condition')
        cls.eventB = M.new_event(action={M.new_action(M._kb.rules['close/c1'], M._entities['P'], M._entities['r_0'],
                                                      M._entities['s_0'], M._entities['c_0'])}, event_style='action')
        cls.questA = M.new_quest(win_event=[cls.eventA, cls.eventB])
        cls.questB = M.new_quest(win_event={'and': [cls.eventA, cls.eventB]})

        # 2. Defining an event and then test the process of adding a Proposition with a verb tense to the state,
        #    using a quest.
        cls.quest0 = M.new_quest(win_event=[cls.eventA])


        cls.eventC = M.new_event(condition={M.new_fact('read/e', M._entities['cpu_0'])},
                                 action={M.new_action(M._kb.rules['check/e1'], M._entities['P'], M._entities['r_0'],
                                                      M._entities['s_0'], M._entities['cpu_0'])},
                                 condition_verb_tense={'read/e': 'has been'}, event_style='condition')
        cls.questC = M.new_quest(win_event=[cls.eventC])

        # 3. Defining two quests, which one is prerequisit for the other one, by adding a has_been Proposition to
        #    the state. Let's test how a game performs with these two quests. If the Proposition isn't in the state
        #    set and an specific action happens, the game should fail. This test also checks if the sequence of
        #    actions happening appropriately.
        cls.eventD = M.new_event(action={M.new_action(M._kb.rules['open/c'], M._entities['P'], M._entities['r_0'],
                                                      M._entities['s_0'], M._entities['c_0'], M._entities['cpu_0'])},
                                 event_style='action')
        cls.eventE = M.new_event(condition={M.new_fact('unread/e', M._entities['cpu_0'])}, event_style='condition')
        cls.eventF = M.new_event(action={M.new_action(M._kb.rules['open/c1'], M._entities['P'], M._entities['r_0'],
                                                      M._entities['s_0'], M._entities['c_0'])},
                                 event_style='action')

        cls.questD = M.new_quest(win_event=[cls.eventD], fail_event={'and': [cls.eventE, cls.eventF]}, reward=2)

        # M.quests = [cls.quest0, cls.questC, cls.questD]
        M.quests = [cls.questC, cls.questD]
        cls.game = M.build()

    def _apply_actions_to_quest(self, actions, quest):
        state = self.game.world.state.copy()
        for action in actions:
            assert not quest.done
            state.apply(action)
            quest.update(action, state)

        return quest

    def test_quest_completed(self):
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # First, let's test an EventOr, if either of its events happen the quest should be completed.
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        quest = QuestProgression(self.questA, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventA.actions, quest)
        assert quest.done
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None

        # Alternative winning strategy.
        quest = QuestProgression(self.questA, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventB.actions, quest)
        assert quest.done
        assert quest.completed
        assert not quest.failed
        assert quest.winning_policy is None

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Second, let's test an EventAnd, if either of its events happen the quest should not be completed. If both
        # events happen, then the quest become completed.
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        quest = QuestProgression(self.questB, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventA.actions, quest)
        assert not quest.done
        assert not quest.completed
        assert not quest.failed
        assert quest.winning_policy is not None

        quest = QuestProgression(self.questB, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventB.actions, quest)
        assert not quest.done
        assert not quest.completed
        assert not quest.failed
        assert quest.winning_policy is not None

        # Winning strategy.
        quest = QuestProgression(self.questB, KnowledgeBase.default())
        quest = self._apply_actions_to_quest([act for acts in [self.eventA.actions, self.eventB.actions] for act in acts], quest)
        assert quest.done
        assert quest.completed
        assert not quest.failed

    def test_quest_failed(self):
        quest = QuestProgression(self.questD, KnowledgeBase.default())
        quest = self._apply_actions_to_quest(self.eventF.actions, quest)
        assert not quest.completed
        assert quest.failed
        assert quest.winning_policy is None

    def test_game_completed(self):
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # First, let's test a quest which adds a verb_tense-based proposition to the state of the game.
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        game = GameProgression(self.game)
        for action in self.eventC.actions:
            assert not game.done
            game.update(action)
        assert self.eventC.traceable[0] in [f for f in game.state.facts]
        assert not game.done

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Second, let's test a series of quests with winning and failing conditions.
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        assert game.winning_policy == self.eventD.actions

        for action in self.eventD.actions:
            assert not game.done
            game.update(action)

        assert game.done
        assert game.completed
        assert not game.failed
        assert game.winning_policy is None
        x = 0

    def test_game_failed(self):
        game = GameProgression(self.game)
        action = self.eventF.actions[0]
        game.update(action)
        assert not game.completed
        assert game.failed
        assert game.done
        assert game.winning_policy is None


def make_test_files(settings: Mapping[str, str], options: Optional[GameOptions] = None):

    kb = KnowledgeBase.load(target_dir=pjoin(os.path.dirname(__file__), 'textworld_data'))
    options = options or GameOptions()
    options.grammar.theme = 'spaceship'
    options.kb = kb

    if settings["level"] == 'test':
        mode = "test"
        options.nb_objects = 4

    metadata = {"desc": "ContentDetection",  # Collect information for reproduction.
                "mode": mode,
                "world_size": options.nb_rooms}

    game_obj = TestContentCheck()
    game_obj.setUpClass(options)
    game_obj.test_quest_completed()
    game_obj.test_quest_failed()
    game_obj.test_game_completed()
    game_obj.test_game_failed()

    game_obj.game.metadata = metadata
    uuid = "tw-test_content-{level}".format(level=str.title(settings["level"]))
    game_obj.game.metadata["uuid"] = uuid

    return game_obj.game


make_test_files({'level': 'test'})

# register(name="tw-test_content",
#          desc="Generate a test file for the content check game",
#          make=make_test_files,
#          add_arguments=build_argparser)
