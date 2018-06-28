# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


VARIABLES_TXT_CONTENT = """
# [variables]
thing: t
room: r
container: c -> t
supporter: s -> t
stove : stove -> s
# This is a comment.
oven: oven -> c
door: d -> t
portable_object: o -> t
key: k -> o
food: f -> o

# [constants]
player: P
inventory: I
"""

RULES_TXT_CONTENT = """
# Navigation #
go/north :: at(P, r) & $north_of(r', r) & $south_of(r, r') & $free(r, r') & $free(r', r) -> at(P, r')
go/south :: at(P, r) & $south_of(r', r) & $north_of(r, r') & $free(r, r') & $free(r', r) -> at(P, r')
go/east  :: at(P, r) & $east_of(r', r) & $west_of(r, r') & $free(r, r') & $free(r', r) -> at(P, r')
go/west  :: at(P, r) & $west_of(r', r) & $east_of(r, r') & $free(r, r') & $free(r', r) -> at(P, r')

# Doors #
unlock/d :: $at(P, r) & $link(r, d, r') & $link(r', d, r) & $in(k, I) & $match(k, d) & locked(d) -> closed(d)
lock/d   :: $at(P, r) & $link(r, d, r') & $link(r', d, r) & $in(k, I) & $match(k, d) & closed(d) -> locked(d)
open/d   :: $at(P, r) & $link(r, d, r') & $link(r', d, r) & closed(d) -> open(d) & free(r, r') & free(r', r)
close/d  :: $at(P, r) & $link(r, d, r') & $link(r', d, r) & open(d) & free(r, r') & free(r', r) -> closed(d)

# Containers) & supporters #
open/c   :: $at(P, r) & $at(c, r) & closed(c) -> open(c)
close/c  :: $at(P, r) & $at(c, r) & open(c) -> closed(c)
insert   :: $at(P, r) & $at(c, r) & $open(c) & in(o, I) -> in(o, c)
take/c   :: $at(P, r) & $at(c, r) & $open(c) & in(o, c) -> in(o, I)
lock/c   :: $at(P, r) & $at(c, r) & $in(k, I) & $match(k, c) & closed(c) -> locked(c)
unlock/c :: $at(P, r) & $at(c, r) & $in(k, I) & $match(k, c) & locked(c) -> closed(c)
put      :: $at(P, r) & $at(s, r) & in(o, I) -> on(o, s)
take/s   :: $at(P, r) & $at(s, r) & on(o, s) -> in(o, I)
take     :: $at(P, r) & at(o, r) -> in(o, I)
drop     :: $at(P, r) & in(o, I) -> at(o, r)

# Misc #
eat :: in(f, I) & edible(f) -> eaten(f)
"""

CONSTRAINTS_TXT_CONTENT = """
c1 :: open(c)   & closed(c) -> fail()
c2 :: open(c)   & locked(c) -> fail()
c3 :: closed(c) & locked(c) -> fail()

d1 :: open(d)   & closed(d) -> fail()
d2 :: open(d)   & locked(d) -> fail()
d3 :: closed(d) & locked(d) -> fail()

obj1 :: in(o, I) & in(o, c) -> fail()
obj2 :: in(o, I) & on(o, s) -> fail()
obj3 :: in(o, I) & at(o, r) -> fail()
obj4 :: in(o, c) & on(o, s) -> fail()
obj5 :: in(o, c) & at(o, r) -> fail()
obj6 :: on(o, s) & at(o, r) -> fail()
obj7 :: at(o, r) & at(o, r') -> fail()
obj8 :: in(o, c) & in(o, c') -> fail()
obj9 :: on(o, s) & on(o, s') -> fail()

k1 :: match(k, c) & match(k', c) -> fail()
k2 :: match(k, c) & match(k, c') -> fail()
k3 :: match(k, d) & match(k', d) -> fail()
k4 :: match(k, d) & match(k, d') -> fail()

r1 :: at(P, r) & at(P, r') -> fail()
r2 :: at(s, r) & at(s, r') -> fail()
r3 :: at(c, r) & at(c, r') -> fail()

# A door can't be used to link more than two rooms.
link1 :: link(r, d, r') & link(r, d, r'') -> fail()
link2 :: link(r, d, r') & link(r'', d, r''') -> fail()

# There's already a door linking two rooms.
link3 :: link(r, d, r') & link(r, d', r') -> fail()

# There cannot be more than four doors in a room.
# dr2 :: at(d1: d, r) & at(d2: d, r) & at(d3: d, r) & at(d4: d, r) & at(d5: d, r) -> fail()

# An exit direction can only lead to one room.
nav_rr1 :: north_of(r, r') & north_of(r'', r') -> fail()
nav_rr2 :: south_of(r, r') & south_of(r'', r') -> fail()
nav_rr3 :: east_of(r, r') & east_of(r'', r') -> fail()
nav_rr4 :: west_of(r, r') & west_of(r'', r') -> fail()

# Two rooms can only be connected once with each other.
nav_rrA :: north_of(r, r') & south_of(r, r') -> fail()
nav_rrB :: north_of(r, r') & west_of(r, r') -> fail()
nav_rrC :: north_of(r, r') & east_of(r, r') -> fail()
nav_rrD :: south_of(r, r') & west_of(r, r') -> fail()
nav_rrE :: south_of(r, r') & east_of(r, r') -> fail()
nav_rrF :: west_of(r, r')  & east_of(r, r') -> fail()

free1 :: link(r, d, r') & free(r, r') & closed(d) -> fail()
free2 :: link(r, d, r') & free(r, r') & locked(d) -> fail()

eaten1 :: eaten(f) & in(f, I) -> fail()
eaten2 :: eaten(f) & in(f, c) -> fail()
eaten3 :: eaten(f) & on(f, s) -> fail()
eaten4 :: eaten(f) & at(f, r) -> fail()
"""

REVERSE_RULES_TXT_CONTENT = """
# Navigation #
go/north : go/south
go/south : go/north
go/east : go/west
go/west : go/east
go/north/d : go/south/d
go/south/d : go/north/d
go/east/d : go/west/d
go/west/d : go/east/d

# Doors #
unlock/d : lock/d
lock/d : unlock/d
open/d : close/d
close/d : open/d

# Containers & supporters #
open/c : close/c
close/c : open/c
insert : take/c
take/c : insert
lock/c : unlock/c
unlock/c : lock/c
put : take/s
take/s : put
take : drop
drop : take

# Misc #
eat : None
"""
