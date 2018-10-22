# Context-Free Grammars

The following document is intended to assist anyone who is interested in writing a custom "flavour" for a textworld. A flavour does not modify the underlying world structure, but instead realizes the world structure to the textual descriptions that will be used in the final game. It is in this way that they can "flavour" the textworld, such as realizing the world as a modern house, or a fantasy castle, etc. The descriptions are built using a context-free grammar.

## Basics
In TextWorld, the context-free grammar is defined simply with the syntax `nonterminal: option1 ; option2 ; etc.`, where each option may be text, a non-terminal symbol, or a mix of symbols and text. As an example, consider the following rule.

```
food: apple; lettuce; cheese
```

In expanding the `food` symbol, the grammar will return either `apple`, `lettuce` or `cheese` with equal likelihood.

A non-terminal symbol may be embedded by enclosing the symbol within `#`.

```
introduction: Hello, #greeting#
greeting:nice to meet you!;how are you?;have we met?
```

In the above rule, if we expand `introduction`, the grammar will recursively expand any rules present in the sentence. So expanding `introduction`, will obtain either `Hello, nice to meet you!`, `Hello, how are you?` and `Hello, have we met?`, with equal probability.

Given the recursive nature of the expansion, we can write something like the following:

```
introduction: Hello, #greeting#
greeting:#greet_how# to meet you!;how are you?;have we met?
greet_how:nice;great;wonderful
```

And when expanding `introduction` we can obtain lines like `Hello, wonderful to meet you!` since the grammar will first expand `greeting` and then `greet_how`. Note that symbols cannot have spaces in them. Also, note that when expanding, spacing will be preserved. Grammars are saved using the `.twf` extension (textworld flavour).

Lastly, comment-lines can be added in the grammar file by making the first character in the line `#`.

```
# This is a comment and not part of the grammar
introduction: Hello, #greeting#
greeting:nice to meet you!;how are you?;have we met?
```


## Flavours

When writing a new flavour for a textworld, we need to author four separate grammar files, one for object name generation, one for room description generation, one for instructions and one for questions. So if we are, for example, writing a space-themed flavour called `spaceship`, we would need to author the following files:

```
spaceship_obj.twf
spaceship_room.twf
spaceship_instruction.twf
spaceship_question.twf
```

Each file has certain requirements and rules, so we will discuss each in more depth in the following sections. You can also refer to `house_obj.twf`, `house_room.twf`, `house_instruction.twf` and `house_question.twf` to see how the `house` flavour is defined.

## Names

In the names folder, we must provide names for all the possible types in our world, ie. the rooms, containers, supporters, foods, burgers, keys, doors, objects, and any additional types that may have been defined.

### Room Types

Worlds in Inform are defined as a series of connected rooms. The text generator allows for the possibility of generating different room *types*, ie. rooms that have certain properties. For example, we might expect to find different objects in a washroom vs. a kitchen. Room types are defined using a special symbol `room_types`, that **must** be present in the object names grammar. As an example, take the `house_obj` room types:

```
room_type:clean;cook;rest;work;storage
```

Here, we define five types of rooms, rooms used for cleaning (eg. washrooms), cooking (eg. kitchens), resting (eg. bedroom), working (eg. office), and storage (eg. cupboards). The number of room types is open, but since we need to define custom objects for each room, it can get burdensome to author a grammar with significant number of room types.

### Naming conventions

Things in the textworld are named using an *adjective* and a *noun*. We define these names using custom symbols, of the form `roomtype_(type)_adj` and `roomtype_(type)_noun`. As an example, if we are defining objects for a clean room type, we would use `clean_(o)`. We could then define the following:

```
clean_(o)_adj:new;old;dusty
clean_(o)_noun:broom;towel;vacuum
```

This means that in a cleaning room, we may find a `new broom`, `old vacuum`, etc. Note that adjectives and nouns **must** be one word only, although hyphens may be used to make compound words. Note that we must define adjectives and nouns for all possible room type and type combinations. This is burdensome, but we also define *general* naming rules to simplify things, and if `roomtype_(type)_adj` and `roomtype_(type)_noun` are not defined, then the grammar will default to the general rules. For example, since we assume all doors will be similar regardless of room in a house, the following is the definition for doors in the `house` flavour.

```
(d)_adj:wooden;oak;birch;maple;balsam;beech;mahogany;walnut;cedar;fir;pine;redwood
(d)_noun:door
```

Thus, since we don't have any specific door rules, the grammar will always generate a door name from the above general rules. For a general naming rule, we need to define `(type)_adj` and `(type)_noun`. This is also customizable, and we can, for example, use custom nouns but with a shared set of adjectives. This was used in the `house` flavour for defining objects.

```
(o)_noun:pencil;pen
(o)_adj:new;old;used;dusty;clean;large;small;fancy;plain;ornate;antique;contemporary;modern;dirty;elegant;immaculate;simple;hefty;modest;gaudy;frilly;decorated;austere

clean_(o)_noun:iron;paper;towel;mat;soap;mop;broom;shirt;sock;vacuum;sponge

storage_(o)_noun:lightbulb;broom;shirt;sock;shoe;glove;hat;cane;scarf

cook_(o)_noun:fork;knife;cup;mug;spoon;bowl;napkin;whisk;ladle;blender;teacup;kettle;teapot;glass

rest_(o)_noun:tv;controller;pillow;blanket;plant;book;dvd;cd;toy;lamp;laptop

work_(o)_noun:pen;pencil;stapler;staple;printer;mouse;keyboard;mug;disk;cd;book;folder;binder
```

Meanwhile, the `castle` flavour defines custom adjectives, to give a custom feel to the objects found in each room:

```
(o)_noun:quill;parchment
(o)_adj:dusty;dirty;filthy;plain;small;hefty;large;imposing;impressive

dark_(o)_noun:skull;manacles;bone;diary;relic;amulet
dark_(o)_adj:stained;warped;twisted;foul;unholy;cursed

magic_(o)_noun:quill;parchment;crystal;wand;book;orb;relic;amulet
magic_(o)_adj:sparkling;glowing;hovering;magical;mysterious

fight_(o)_noun:sword;bow;quiver;chestplate;helmet;knife;shield
fight_(o)_adj:hefty;sturdy;large;imposing;impressive;durable

royal_(o)_noun:coin;crown;cape;scepter;necklace;chalice;amulet
royal_(o)_adj:frilly;decorated;austere;elegant;immaculate;ornate;intricate

servant_(o)_noun:tunic;hat;pitchfork;scythe;parchment;diary
servant_(o)_adj:dusty;dirty;filthy;plain;small
```

Note that the general rules will always be used for objects that are not tied to any particular room. For example, the player starts with an inventory of items, and these are all generated using the general rules since they do not belong to any particular room type.

### Note on the Player

As a slight quirk, all grammars will need to define a noun and adjective for the player. However, since we do not make use of these values, they are left as "None". Simply add the following two lines to the grammar to achieve this effect:
```
(P)_noun:None
(P)_adj:None
```

### Matching Adjectives

Adjectives for keys are specially generated. In every name grammar, the symbol `match` **must** be defined and must contain a list of adjectives that are *not used elsewhere in the grammar*. During generation, when a key is found, it and its matching container or door will gain the same adjective. As an example, given the rule below:
```
match:red;green;blue
```
Means that if we see, say, a `red chest`, then we know we can unlock it with a `red` key, and same for a `blue door` and `blue key`, etc. Typically, we should define ~10 different unique adjectives for matches to reduce the possibility of repetition (worlds with a high number of keys are unlikely). Note that some regular adjectives for keys should also be defined, in the case that a key is generated that is not matched to any container or door (and is thus a distractor).

### Object Descriptors
Object descriptors must be defined, and will be the output provided if the player *examines* the particular object. We therefore must define a `(type)_desc` for each of our possible types. Some examples from the `house` flavour are:

```
(c)_desc:The (name) looks strong, and impossible to force open.

(s)_desc:The (name) is #supp_stable#.
supp_stable:stable;wobbly;unstable;balanced;durable;reliable;solid;undependable
```

Which gives descriptions for the `c` type (containers), and `s` type (supporters). These are mostly distractor texts and can even be set to `None`, although the symbol itself must be defined. We must also define two symbols `openable_desc` and `on_desc`, which are special functions used to provide additional information about the contents of a container/supporter or state of a container/door (see Inform 7 Functions for details). The following are the descriptors from the `house` flavour.

```
openable_desc:[if open]It is open.[else if locked]It is closed.[otherwise]It is locked.
on_desc:On the (name), is [a list of things on the (name)].
```

Note that whenever we are describing a particular object, we will keep track of the object we are describing. If we want to include some properties of the object in the description, we can do this using `(name)`, `(name-adj)` or `(name-n)`, which will print the full name, adjective or noun only of the object we are describing. So `You see a (name).`, `You see a (name-adj) thing. It looks like a (name-n)`, would give `You see a red door` and `You see a red thing. It looks like a door` for the object `red door`. This will be also useful in the next section when we are describing objects in the room. Note, however that the grammar only understands this syntax for descriptors, and so they cannot be used in the question or instruction files.

## Rooms

During generation, we create descriptions for each room. The generation always follows a general pattern in that it first generates a line describing the room object, followed by list of all the objects in the room (that are not in containers or on shelves), followed by a list of the exits. We cover each in turn below, with special sections on "Multiple Objects" and "Exits" which are slightly more complex and have specific syntax.

### Basics
The first symbol that must be defined for a room is `dec` is the description of the room object. For example `You enter the (name)` will give `You enter the messy kitchen` for a room called `messy kitchen`. Following this, the generator will generate a description for each of the visible objects in the room. There are currently only two objects that will be immediately visible, containers and supporters, all other objects are found either in the containers or on the supporters. This means we only need to define two additional symbols `room_desc_(c)` and `room_desc_(s)`, note that if the world generation is modified to add additional objects to the room, then we would need to add symbols for them. `(name)`, `(name-adj)` and `(name-n)` may all be used here to refer to the object we are describing.

### Multiple Objects
The generator has limited support for grouping objects together. It will try to group together objects according to shared adjectives or nouns. For groupings, we will need to define a single symbol `room_desc_group`, and custom `room_desc_(type)_multi_noun` and `room_desc_(type)_multi_adj` for each `type` that might appear multiple times in a room. Since the only objects that are considered are containers and supporters this means we have to define `room_desc_(c)_multi_noun`, `room_desc_(c)_multi_adj`, `room_desc_(s)_multi_noun` and `room_desc_(s)_multi_adj`.

Mutliple object line generation occurs as follows, first, it finds grouped objects, and then will write the `room_desc_group` symbol. Followed by a `room_desc_(type)_multi_noun` description for each object if they are grouped by adjective, or `room_desc_(type)_multi_adj` if they are grouped by noun.

`room_desc_group` has some special functionality for it to handle plurality. First, it has to special symbols `(^)` and `(val)` and understands `(name)` differently than elsewhere. `(^)` is a quantifier that will convert the number of grouped objects into a text value, so 1 = "one", 2 = "two" and anything higher is "several". `(val)` will represent what we are grouping by, so if we are grouping by nouns it'll be the plural of the noun we are grouping by (e.g. "chests"), and for adjectives it'll be the plural of the adjective (e.g. "red things"). `(name)`, here, will be a list of the grouped objects, e.g. ("a chest, a crate and a box" for nouns). As a practical example, take the symbol definition from `house_room.twf`:

```
room_desc_group:There are (^) (val) here, (name).
```

This will expand to, for example, `There are two red things here, a chest and a box` if we have a `red chest` and a `red box` in the same room. It would expand to `There are two chests here, one red and one blue.` if we have a `red chest` and a `blue chest` in the same room.

The `room_desc_(type)_multi_noun/adj` do not have any special handling and can be authored as usual. They will be listed sequentially after the `room_desc_group` symbol.

### Exits
Exits are automatically grouped together into a single phrase, so we would get `There are exits to the east and north` as opposed to `There is an exit to the east. There is an exit to the north.`. This is similar to the multiple object grouping described above, and there is special handling to deal with the plurality problems. Specifically, there are three symbols which must be defined, `room_exit_desc`, `room_(d)_exit_desc_alt`, and `room_(d)_exit_desc`. The rules are as follows, if we have only exits that don't have doors, then we will expand `room_exit_desc`. If we have only exits with doors, then we use `room_(d)_exit_desc_alt`. Otherwise we list the exits using `room_exit_desc` and then use `room_(d)_exit_desc` to list the exits that have doors.

There are also special symbols and handling for these symbols, as with `room_desc_group`. In this case `(dir)` is the list of directions the list of exits leads, and `(name)`, `(name-n)` and `(name-adj)` refer to the lists of doors or door properties, in cases where we are defining doors. We also make use of a special embedded function `[a|b]` which is a context-sensitive function which, when expanding, will take the text from the left-hand side, `a`, if we are only referring to one object and the right-hand side, `b`, otherwise. As an example `There [is a door|are doors] here` would expand to `There is a door here` if we only have one door and `There are doors here` otherwise. As an example, take a subset of the definitions from the `house` flavour:

```
room_exit_desc:There [is an exit|are exits] to the (dir).
room_(d)_exit_desc_alt:There [is a door|are doors], (name-adj), leading (dir).
room_(d)_exit_desc:The [exit|exits] to the (dir) [is|are] blocked by (name).
```

If we have one east exit, the generator will expand `room_exit_desc` to `There is an exit to the east`. If we had an east and north exit, and an exit to the west with a door, then we would get `There are exits to the east and north. The exit to the west is blocked by a door.` after the system expands `room_exit_desc` followed by `room_(d)_exit_desc`

## Instructions

Instructions grow linearly with actions, in the sense that we typically need one symbol per action. This symbol is usually just the name of the action. Currently, that means there must be symbols for take, insert, put, eat, open, close, unlock, lock, go/north, go/south, go/east, go/west, go/north/d, go/south/d, go/east/d, go/west/d and wait. When we generate lines of text, we keep track of what objects are involved and they can be referred to by using parentheses. For example, in `unlock` we can refer to the key by `(k)`. When generating instructions, the system will automatically make certain names ambiguous to make the instructions harder to figure out, e.g. referring to a `red key` just as `a key`. Ambiguity, however, is handled automatically and whatever ambiguity is selected, it will simply replace `(k)` with the result.

Slightly more complex is the idea of object groups. This is a specific syntax to instructions and handles situations where certain actions may have different components. For example, we can `unlock` a door or container. For instructions, we use the syntax `(c|d)`, to state that, when expanding, replace this symbol by *either* the container or the door depending on what is involved in the action. We can use this for multiple objects, for example `(o|k|f|b)` refers to all the objects that can be in containers or on shelves, and are therefore specific to take, insert and put.

### Compound Actions
The generator can handle blending together actions that refer to the same set of objects. For example, rather than writing separate instructions for `Unlock chest with key` and `open chest`, the instructions can simply be written `Open chest with key`. There are a number of ways that instructions can be combined, and it will **only** combine instructions if it finds a matching symbol for the specific compound instructions.

We do this using the prefix `ig_` followed by a list of the actions separated by `_`. So for the example, we would create a symbol `ig_unlock_open` to handle the example above. In this manner, we are able to control which instructions are possible to combine, while also avoiding potential crashes if a certain combination of instructions was not predicted. Below we give a list of useful compound descriptions that are used in most of the `instruction` grammars:

```
ig_unlock_open: Unlocking and opening either a door or container.
ig_unlock_open_take: Unlock, open a container and take something out of it.
ig_open_take: Open a closed container and take something out of it.
ig_take_unlock:Take a key and use it to unlock a door or container.
ig_open_insert:Open a container and insert something into it.
ig_insert_close:Insert something into a container and then close the container.
ig_close_lock:Close a container or door and then lock it.
```

## Inform 7 Functions

Inform 7 has some specific built-in functions that we may make use of for our grammar, mainly for listing the contents of a container or supporter. To list the objects of a container, say a `chest`, we would write `[a list of things in the chest]`. So, if the container had a pen and an apple in it, when running in Inform the text would print `a pen and an apple`. A better list of such commands is below

```
# Containers
In the chest [is-are a list of things in the chest]. -> In the chest are a pen and an apple.
The chest has [a list of things in the chest] in it. -> The chest has a pen and an apple in it.

# Supporters
On the shelf [is-are a list of things on the shelf]. -> On the shelf are a pen and an apple.
The shelf has [a list of things on the shelf]. -> On the shelf are a pen and an apple.
```

This is useful for dynamically listing contents, for example if the player takes the apple from the chest, then the description will be updated automatically to read `The chest has a pen in it`.

A similarly useful function for containers and doors is the `[if x is open][else if x is locked][otherwise][end if]` which will modify the sentence based on the state of the object. For example, for our chest we could say `The chest is [if chest is open]open[else if chest is locked]locked[otherwise]closed[end if].` When writing the line of text, Inform will automatically select the line which matches the if statement, so an open chest will result in `The chest is open`, a locked chest will result in `The chest is locked.`, etc (note that `open`, `closed` and `locked` are the three possible states of a container or door). We can also embed functions within each other, so `The chest is [if chest is open]open, and has [a list of things in the chest] in it.[else if chest is locked]locked[otherwise]closed[end if].` will also print a list of the chest's contents if the chest is open.

## Interesting Properties
Using a grammar allows for several interesting aspects of natural language. These all emerge out of the way the grammar is authored, and some are supported by underlying systems (e.g. Grouping similar objects)
* **Language Variability**: The most basic property of a grammar is that we have multiple ways to represent the same information. This allows for significant variation within the generated descriptions.
* **Paraphrasing**: By using features such as grouping or adjective/noun only references, it is possible to present shorter or longer, and more or less detailed representations of the same information.
* **Coreference**: By using multiple sentences for describing an object, we can use pronoun references such as "it", which must be resolved to the correct object in order for the information to make sense. eg `There is a chest. It is red` vs. `There is a red chest.`
* **Entailment**: We can avoid listing certain information that can be concluded from other pieces of evidence. For example, if the contents of the container are listed, then we expect that the container is open.
* **Ambiguity**: Using elements such as paraphrasing, grouping, coreference and other writing techniques, we can write information that is very ambiguous `There is a container in the room. It is red. It also has a pen in it.` or more specific `There is an open red chest in the room. The open red chest has a pen in it`. Likewise, grouping can introduce complex ambiguities, for example `There are two chests in the room, a red one and a blue one. The red one has a pen in it.` indicates that we have a red chest and a blue chest, and that the red chest is open and has a pen and the blue chest is either locked or closed.
* **Distractors**: It is very easy to add decorative but meaningless text into a description that an agent must learn to ignore, for example `A chest, barely noticeably red underneath layers of dust and cobwebs, lies dormant in a forgotten corner.` really only contains the basic knowledge that a red chest is in the room (although likely more interesting to read for human players).
