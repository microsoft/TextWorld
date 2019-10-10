Chapter 2 : How To Design A New Text Grammar
==============================================
In addition to logic files, each game requires a grammar file in which it describes various sentences to be used within
the game. For example, when the player enters a room, a few lines of the greetings to the game, introduction of the
room, the items inside the room, etc. are displayed for the player. This text is compiled by a word parser at Inform7
using a customized text-grammar file. This file also should be designed by the designer of the game and stored with
`.twg` extension.

To describe this file, it is better to start with greetings. Greetings is a set of various sentences which will be
picked by the parser randomly and will be displayed on output anytime the player either enters into the game or enters
into a room. The greeting should include a general description about the state of the game, the room, or the current
elements of the game. If the generated sentence requires importation of elements or status of the game, that should
also be coded into the sentence. The question is how? Here, we practice writing such sentences.

Let's first explore a fixed type of greetings.

.. code-block:: bash

    GREETING : GREETING!;GREETINGS TREKKIE!;HELLO ASTRONAUT!;ALRIGHT THEN!; HEY  TREKKIE

Here, `GREETING` is the code to call the greeting sentence and the right side of semicolon is an array-like of different
options that the parser can pick between them; e.g. in above example, there are five different options and each time the
parser randomly picks one of them as the greeting of the game. Each of these five has the same probability; thus, if we
want to increase the probability of one item, we can repeat that as much as we wish. Moreover, each phrase above is
fixed and will be used as it is. However, it is possible to have a sentence which can be reformed based on the
situation. Following is an example of flexible greeting,

.. code-block:: bash

    Flex_greeting : #GREETING#, it is TextWorld

This example explains that we may have "Greeting!, it is TextWorld" or "HEY  TREKKIE!, it is TextWorld", or any other
combinations that we can mix and match from "Flex_greeting" and "GREETING". In other words, any word (or combination of
words which are attached by hyphen) and comes in between "#", is like a symbol of another vector of phrases and is
replaced by the parser with one of the phrases from that vector. Following is another example of the creation of the
flexible sentence:

.. code-block:: bash

    dec : #GREETING# #dec_type##suffix_(r)#;#dec_type##suffix_(r)#

    dec_type : #reg-0#;#difficult-0#
    suffix_(r) : . Okay, just remember what is your mission here to do, and everything will go great.; \
                 . You try to gain information on your surroundings by using a technique you call 'looking.'; \
                 . You can barely contain your excitement.;
                 . The room seems oddly familiar, as though it were only superficially different from the other rooms in the spacecraft.; \
                 . You decide to just list off a complete list of everything you see in the module, because hey, why not?;

    reg-0       : #01#;#02#
    difficult-0 : #03#

    01 : #dec_find-yourself# in a (name);#dec_guess-what# (name)
    02 : Well, here we are in #dec_a_the# (name)
    03 : You're now in #dec_a_the# (name)

    dec_find-yourself : You #dec_what#
    dec_guess-what    : #dec_well-guess#, you are in #dec_a_the# place we're calling #dec_a_the#
    dec_a_the         : a;the
    dec_what          : are;find yourself;arrive
    dec_well-guess    : Guess what;Well how about that;Well I'll be

In this example, assume that the #GREETING# #dec_type##suffix_(r)# is randomly picked, to replace GREETING, dec_type,
and suffix_(r) variables, respectively, the "HELLO ASTRONAUT!", "reg-0", and ". Okay, just remember what is your mission
here to do, and everything will go great." are chosen. To replace reg-0, the parser randomly picks "02", and to replace
"02", the "Well, here we are in #dec_a_the# (name)" is selected. In the latter choice of phrase we have two type of
variables, one is "dec_a_the" and the other is "(name)". The first has already described and let's assume that "the" is
picked. For the second, the (name) is replaced by the name of a room that the player is in. Rooms and their names are
described in next chapter. Finally, the created sentence is as follows:

.. code-block:: bash

    HELLO ASTRONAUT! Well, here we are in the (name). Okay, just remember what is your mission here to do, and everything will go great.

This sentence is made for a sample state and anytime the game reaches to this state the (name) is replace with the
corresponding room's name and is printed on the screen. To increase the variety of the outputs, a designer can expand
those sentence block to more and more options. However, it is always important to notice that these sentences
should comply with the scenario of the game in general and the specific scene of the game in each state. We recommend
to make a good use of general sentences, and specific type of sentences which can be fed by variable from the game
state (between parentheses variables). Following this advice can give better sentence in accordance to the game story.

Although the design of a text-grammar file is more depend on the designer's preference rather than the logic file, yet,
there are some sections which should be considered in .twg file. The fundamental sections are named as

    1. Expandables  	        : All required combinations, structures, etc of words, letters, and numbers which are used in the whole text of the grammar.
    2. Verbs         	        : All verbs which are used as action or simply as verb in the text are collected.
    3. Types & Variables        : Type of objects and variables of the game are defined and coded.
    4. Objects Garmmar	        : The grammar of each object of the game is defined in this section.
    5. Room Description Grammar : All the texts which are used to describe the game inside different rooms are defined and expanded.
    6. Instructions Grammar     : The grammar of instructions for compound commands, etc are described.

Expandables are all the variables which comes in between "#"s and expand to create a sentence. Verbs are also some sort
of expandable in which different synonyms and tense of the verb and its corresponding synonyms are clarified to be used
in text creation and hesitate from repeating a verb frequently, see below example for "take" verb,

.. code-block:: bash

    take        : #take_syn_v# the #obj_types# from the (r).;#take_syn_v# the #obj_types# that's in the (r).
    take_syn_v  : take;retrieve;grab
    take_syn_pp : taken;got;picked
    taking      : taking;getting;picking

    take/s      : #take_syn_v# the #obj_types# from the #on_var#.

    take/c      : #take_syn_v# the #obj_types# from the #on_var#.

"take_syn_v" and "take_syn_pp" respectively refer to the list of synonyms and the past participle of those
synonyms; the ing-form of the verb is the following line. Similar to the logic file description, if we have to assign a
word in different application, like take vs. take from a table, these two can be distinguished by assigning different
code words for each set. To understand this, take a look at above example and compare the definition of "take" with
"take/s".

Types of all elements in the game can be coded for the grammar to address much easier. For example, "obj_types : (o|k|f)"
indicates all the object, key, or food with the `obj_types`, while "on_types : (c|s)" refers to container or supporter
types which object-like can be put `on` it. Recall that the left-side of the semicolon is just a symbolic way of
representing something which comes on the left-side; so, it is just for text generation and there is no logic behind it.

In "Objects Grammar" section, every element of the game can have their own grammar and customized nouns and adjectives
to create more sense of the world that the designer tries to build. As an instance, a room can generally be expanded by
an adjective and a noun; if the game refers to an office (work type of room), then the list of adjective-noun pairs
could be different, and based on the game story, the designer can add as much as combinations she/he wishes, to add
more flavour to her/his game. Below is a good example of how different rooms can be assigned with their
own grammar,

.. code-block:: bash
    # --- Rooms ---------------------------------------------------------------------
    ##   List each type of room with a ';' between each
    ##   Each roomType must have specific rooms
    ###  Creating a room: first, take the name of the roomtype as listed under #room_type# (let's call it X for now).
    ###                   Then, create three symbols with this: X_(r), X_(r)_noun, and X_(r)_adj.
    ###                   X_(r) will always be composed of X_(r)_adj | X_(r)_noun. If you want to subdivide a roomtype into two or more variants, you can add _type1, _type2, etc at the end of the noun and adj symbols.
    ###                   Make sure that these changes are also accounted for in the X_(r) token.

    room_type : clean;cook;rest;work;storage

    (r)       : #(r)_adj# | #(r)_noun#
    (r)_noun  : sleep station;crew cabin;washroom;closet;kitchenette;module;lab;lounge
    (r)_adj   : nondescript;plain

    ### >  Rest Room
    ### >> Sleep Room
    rest_(r) : #rest_(r)_adj_type_1# | #rest_(r)_noun_type_1#;#rest_(r)_adj_type_2# | #rest_(r)_noun_type_2#

    rest_(r)_noun_type_1 : sleep station;sleep station;sleep station;sleeping bag;crew cabin
    rest_(r)_adj_type_1  : cozy;relaxing;pleasant;sleepy
    ### >> fun with friends
    rest_(r)_noun_type_2 : lounge;playroom;recreation zone;crew cabin;crew cabin;crew cabin
    rest_(r)_adj_type_2  : fun;entertaining;exciting;well lit;silent

Majority of the text which is created by the parser belongs to the description of a room. The Room Description Grammar
expands all the grammar which is used for a room to describe the room as well as the scenario at that room. This process
is very similar to what we described in Greetings section.

Last but not least is the "Instructions Grammar". This part basically includes all the required grammatical structures
which the text-based game needs to compound two actions (like unlock and open), separate two sentence from each other or
to connect them with a word, etc. which are important in the expansion of the sentences all over the game. Following is
a few examples of what is designed for the Spaceship game:

.. code-block:: bash
    # --- Compound Command Description Functions ------------------------------------
    ig_unlock_open      : open the locked #lock_types# using the (k).; \
                          unlock and open the #lock_types#.; \
                          unlock and open the #lock_types# using the (k).; \
                          open the #lock_types# using the (k).
    ig_unlock_open_take : open the locked #lock_types# using the (k) and take the #obj_types_no_key#.; \
                          unlock the #lock_types# and take the #obj_types_no_key#.; \
                          unlock the #lock_types# using the (k), and take the #obj_types_no_key#.; \
                          take the #obj_types_no_key# from within the locked #lock_types#.

    # --- Separators -----------------------------------------------------------------
    ##  *--- Action separators
    action_separator_take : #afterhave# #take_syn_pp# the #obj_types#, ; \
                            #after# #taking# the #obj_types#, ; \
                            With the #obj_types#, ; \
                            If you can get your hands on the #obj_types#, ; \
                            #emptyinstruction#;
    action_separator_eat  : #afterhave# #eat_syn_pp# the #eat_types#, ; \
                            #after# #eating# the #obj_types#, ; \
                            #emptyinstruction#;

    ##  *--- Separator Symbols
    afterhave : After you have;Having;Once you have;If you have
    after     : After;

For further details on these expandables, please check the TextWorld's Spaceship game.
