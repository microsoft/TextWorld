# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from textworld.generator.data import KnowledgeBase
from textworld.logic import Proposition, State, Variable


def check_state(state):
    fail = Proposition("fail", [])

    constraints = state.all_applicable_actions(KnowledgeBase.default().constraints.values())
    for constraint in constraints:
        if state.is_applicable(constraint):
            # Optimistically delay copying the state
            copy = state.copy()
            copy.apply(constraint)

            if copy.is_fact(fail):
                return False

    return True


def test_constraints():
    kb = KnowledgeBase.default()

    # Declare some variables.
    P = Variable("P", "P")
    I = Variable("I", "I")
    bedroom = Variable("bedroom", "r")
    kitchen = Variable("kitchen", "r")
    rusty_key = Variable("rusty key", "k")
    small_key = Variable("small key", "k")
    wooden_door = Variable("wooden door", "d")
    glass_door = Variable("glass door", "d")
    chest = Variable("chest", "c")
    cabinet = Variable("cabinet", "c")
    counter = Variable("counter", "s")
    robe = Variable("robe", "o")

    # Doors can only have one state.
    door_states = ["open", "closed", "locked"]
    for door_state in door_states:
        state = State(kb.logic, [Proposition(door_state, [wooden_door])])
        assert check_state(state)
        for door_state2 in door_states:
            if door_state == door_state2:
                continue

            state2 = state.copy()

            state2.add_fact(Proposition(door_state2, [glass_door]))  # New door
            assert check_state(state2)

            state2.add_fact(Proposition(door_state2, [wooden_door]))
            assert not check_state(state2)

    # Containers can only have one state.
    container_states = ["open", "closed", "locked"]
    for container_state in container_states:
        state = State(kb.logic, [Proposition(container_state, [chest])])
        assert check_state(state)
        for container_state2 in container_states:
            if container_state == container_state2:
                continue

            state2 = state.copy()

            state2.add_fact(Proposition(container_state2, [cabinet]))  # New container
            assert check_state(state2)

            state2.add_fact(Proposition(container_state2, [chest]))
            assert not check_state(state2)

    # A player/supporter/container can only be at one place.
    for obj in [P, chest, counter]:
        assert check_state(State(kb.logic, [Proposition("at", [obj, kitchen])]))
        assert check_state(State(kb.logic, [Proposition("at", [obj, bedroom])]))
        assert not check_state(State(kb.logic, [
            Proposition("at", [obj, kitchen]),
            Proposition("at", [obj, bedroom])
        ]))

    # An object is either in the player's inventory, in a container or on a supporter
    obj_locations = [Proposition("in", [robe, I]), Proposition("in", [robe, chest]), Proposition("on", [robe, counter])]
    for obj_location in obj_locations:
        assert check_state(State(kb.logic, [obj_location]))
        for obj_location2 in obj_locations:
            if obj_location == obj_location2:
                break

            state = State(kb.logic, [obj_location, obj_location2])
            assert not check_state(state), "{}, {}".format(obj_location, obj_location2)

    # Only one key can match a container and vice-versa.
    assert check_state(State(kb.logic, [Proposition("match", [rusty_key, chest])]))
    assert not check_state(State(kb.logic, [
        Proposition("match", [small_key, chest]),
        Proposition("match", [rusty_key, chest])]))
    assert not check_state(State(kb.logic, [
        Proposition("match", [small_key, cabinet]),
        Proposition("match", [small_key, chest])]))

    # Only one key can match a door and vice-versa.
    assert check_state(State(kb.logic, [Proposition("match", [rusty_key, chest])]))
    assert not check_state(State(kb.logic, [
        Proposition("match", [small_key, wooden_door]),
        Proposition("match", [rusty_key, wooden_door])]))
    assert not check_state(State(kb.logic, [
        Proposition("match", [small_key, glass_door]),
        Proposition("match", [small_key, wooden_door])]))

    # A door can't be used to link more than two rooms.
    door = Variable("door", "d")
    room1 = Variable("room1", "r")
    room2 = Variable("room2", "r")
    room3 = Variable("room3", "r")
    assert not check_state(State(kb.logic, [
        Proposition("link", [room1, door, room2]),
        Proposition("link", [room1, door, room3]),
    ]))

    door1 = Variable("door1", "d")
    door2 = Variable("door2", "d")
    room1 = Variable("room1", "r")
    room2 = Variable("room2", "r")
    assert not check_state(State(kb.logic, [
        Proposition("link", [room1, door1, room2]),
        Proposition("link", [room1, door2, room2]),
    ]))


def test_room_connections():
    kb = KnowledgeBase.default()

    room0 = Variable("room0", "r")
    room1 = Variable("room1", "r")
    room2 = Variable("room2", "r")

    # Only one connection can exist between two rooms.
    # r1
    # |
    # r0 - r1
    state = State(kb.logic, [
        Proposition("north_of", [room1, room0]),
        Proposition("south_of", [room0, room1]),
        Proposition("east_of", [room1, room0]),
        Proposition("west_of", [room0, room1])
    ])

    assert not check_state(state)

    # Non Cartesian layout are allowed.
    # r1
    # |
    # r0 - r2 - r1
    state = State(kb.logic, [
        Proposition("north_of", [room1, room0]),
        Proposition("south_of", [room0, room1]),
        Proposition("east_of", [room2, room0]),
        Proposition("west_of", [room0, room2]),
        Proposition("east_of", [room1, room2]),
        Proposition("west_of", [room2, room1])
    ])

    assert check_state(state)

    # A room cannot have more than 4 'link' propositions.
    room3 = Variable("room3", "r")
    room4 = Variable("room4", "r")
    room5 = Variable("room5", "r")
    door1 = Variable("door1", "d")
    door2 = Variable("door2", "d")
    door3 = Variable("door3", "d")
    door4 = Variable("door4", "d")
    door5 = Variable("door5", "d")

    state = State(kb.logic, [
        Proposition("link", [room0, door1, room1]),
        Proposition("link", [room0, door2, room2]),
        Proposition("link", [room0, door3, room3]),
        Proposition("link", [room0, door4, room4]),
        Proposition("link", [room0, door5, room5])
    ])

    assert not check_state(state)
