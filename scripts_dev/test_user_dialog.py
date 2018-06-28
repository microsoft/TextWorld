# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from typing import List

from textworld.logic import Action, Proposition, State
from textworld.generator.user_query import query_for_important_facts


# noinspection PyAbstractClass
class FakeState(State):
    def __init__(self, parrot_facts: List[Proposition]):
        super().__init__()
        self._facts = parrot_facts

    @property
    def facts(self):
        return self._facts


# generate fake propositions
propositions = []
for i in range(3):
    new_prop = Proposition(name='thing %d' % (i,))
    propositions.append(new_prop)
fake_state = FakeState(propositions)

# run the test
action = Action(name='Test action', preconditions=[], postconditions=propositions)
facts = query_for_important_facts(actions=[action], last_game_state=fake_state)
print(facts)
