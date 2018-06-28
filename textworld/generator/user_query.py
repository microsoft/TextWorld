# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


"""
User interface using urwid
"""
from typing import List, Optional, Dict
import urwid
from itertools import compress

from textworld.generator.game import EntityInfo
from textworld.logic import Proposition, State, Action, Signature
from more_itertools import flatten


class UrwidWarningDialog(urwid.WidgetWrap):
    """
    Generic message dialog with no text, suitable for warnings.
    """
    signals = ['close']

    def __init__(self, msg_text: str):
        message_text = urwid.Text(msg_text)
        close_button = urwid.Button('Close')
        urwid.connect_signal(close_button, 'click', lambda _: self._emit('close'))

        pile = urwid.Pile([message_text, close_button])
        fill = urwid.Filler(pile)
        super().__init__(urwid.AttrWrap(fill, 'popbg'))


class UrwidQuestQuerier(urwid.PopUpLauncher):
    """
    UI class for query_for_important_quests
    """
    def __init__(self, checkboxes: List[urwid.CheckBox]):
        self.checkboxes = checkboxes
        self.action_cancelled = False

        # set up user interaction
        label = urwid.Text('Select which final facts caused you to win the game:')
        confirm_button = urwid.Button('Confirm', on_press=self.confirm_button_clicked)
        cancel_button = urwid.Button('Cancel', on_press=self.cancel_button_clicked)

        # layout
        combined_pile = urwid.Pile([label] + self.checkboxes + [confirm_button, cancel_button])
        filler = urwid.Filler(combined_pile)
        super().__init__(filler)

    def confirm_button_clicked(self, _):
        checked_boxes = [cb.state for cb in self.checkboxes if cb.state]
        if len(checked_boxes) == 0:
            self.open_pop_up()
        else:
            raise urwid.ExitMainLoop()

    def cancel_button_clicked(self, _):
        self.action_cancelled = True
        raise urwid.ExitMainLoop()

    def create_pop_up(self):
        must_select_dialog = UrwidWarningDialog('You must select at least one fact')
        urwid.connect_signal(must_select_dialog, 'close', lambda _: self.close_pop_up())
        return must_select_dialog

    def get_pop_up_parameters(self):
        return {'left': 0, 'top': 1, 'overlay_width': 32, 'overlay_height': 7}


def query_for_important_facts(actions: List[Action],
                              facts: Optional[List[Proposition]] = None,
                              varinfos:Optional[Dict[str, EntityInfo]] = None) -> Optional[List[Proposition]]:
    """ Queries the user, asking which facts are important.

    Args:
        actions: Actions used to determine or extract relevant facts.
        facts: All facts existing at the end of the game.
    
    Returns:
        The list of facts that are required to win;
        or `None` if `facts` was not provided;
        or `None` if the user cancels.
    """
    if facts is None:  # No facts to choose from.
        return None

    present_facts = set(facts)
    all_postconditions = set(flatten(a.postconditions for a in actions if a is not None))
    relevant_facts = sorted(all_postconditions & present_facts)

    def _get_name(var):
        if varinfos is not None and var.name in varinfos:
            if varinfos[var.name].name is not None:
                return varinfos[var.name].name

        return var.type

    # set up boxes
    checkboxes = []
    for fact in relevant_facts:
        signature = Signature(fact.name, [_get_name(var) for var in fact.arguments])
        fact_str = str(signature)
        cb = urwid.CheckBox(fact_str)
        checkboxes.append(cb)

    # run
    quest_querier = UrwidQuestQuerier(checkboxes)
    loop = urwid.MainLoop(quest_querier, [('popbg', 'white', 'dark blue')], pop_ups=True)
    loop.run()

    if quest_querier.action_cancelled:
        return None  # don't return, even if the user selected items
    else:
        checked_facts = list(compress(relevant_facts, [cb.state for cb in checkboxes]))
        return checked_facts
