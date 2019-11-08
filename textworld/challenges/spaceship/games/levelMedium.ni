Use MAX_STATIC_DATA of 500000.
When play begins, seed the random-number generator with 1234.

button-like is a kind of thing.
container is a kind of thing.
door is a kind of thing.
object-like is a kind of thing.
supporter is a kind of thing.
CPU-like is a kind of object-like.
food is a kind of object-like.
key is a kind of object-like.
cloth-like is a kind of object-like.
text-like is a kind of object-like.
A button-like can be either pushed or unpushed. A button-like is usually unpushed. A button-like is fixed in place.
containers are openable, lockable and fixed in place. containers are usually closed.
door is openable and lockable.
object-like is portable.
supporters are fixed in place.
A CPU-like can be either read or unread. A CPU-like is usually unread.
food is edible.
cloth-like are wearable. cloth-like can be either clean or dirty. cloth-like are usually clean. cloth-like can be either worn in or worn out. cloth-like are usually worn out.
A text-like can be either read or unread. A text-like is usually unread.
A room has a text called internal name.


Understand the command "check" as something new. 
Understand "check email" as checking email. 
checking email is an action applying to nothing. 

Carry out checking email: 
	if a CPU-like (called pc) is unread:                     
		if a random chance of 1 in 4 succeeds: 
			Now the pc is read; 
			Say "Email: Your mission is started.";                                                                       
		otherwise:
			Say "No emails yet! Wait.".  


connectivity relates a button-like to a door. The verb to pair to means the connectivity relation. 

Understand the command "push" as something new. 
Understand "push [something]" as _pushing. 
_pushing is an action applying to a thing.  

Carry out _pushing: 
	if a button-like (called pb) pairs to door (called dr): 
		if dr is locked:
			Now the pb is pushed;                 
			Now dr is unlocked; 
			Now dr is open; 
		otherwise:
			Now the pb is unpushed;                 
			Now dr is locked.

Report _pushing: 
	if a button-like (called pb) pairs to door (called dr): 
		if dr is unlocked:
			say "You push the [pb], and [dr] is now open.";
		otherwise:
			say "You push the [pb] again, and [dr] is now locked."                    


Understand the command "wear" as something new. 
Understand "wear [something]" as _wearing. 
_wearing is an action applying to a thing.  

Carry out _wearing: 
	if a cloth-like (called cl) is worn out:                     
		Now the cl is worn in;                                                                       
	otherwise:
		Say "You have this cloth on.". 


Understand the command "read" as something new. 
Understand "read [something]" as _reading. 
_reading is an action applying to a thing. 

Carry out _reading: 
	if a text-like (called tx) is unread: 
		Now the tx is read; 


Understand "tw-set seed [a number]" as updating the new seed. 
Updating the new seed is an action applying to a number.
Carry out updating the new seed:
	seed the random-number generator with the number understood.


The r_2 and the r_1 and the r_3 and the r_5 and the r_4 and the r_0 and the r_6 and the r_7 are rooms.

The internal name of r_2 is "European Module".
The printed name of r_2 is "-= European Module =-".
The European Module part 0 is some text that varies. The European Module part 0 is "This room belongs to European scientists. Isn't it cool? what do they research? well, we can explore it later... For now, there is a key code here. This code opens the box in the next room and consequently takes you to the next stage. So, explore the table to find the key.".
The description of r_2 is "[European Module part 0]".

The r_1 is mapped west of r_2.
The internal name of r_1 is "US LAB".
The printed name of r_1 is "-= Us Lab =-".
The US LAB part 0 is some text that varies. The US LAB part 0 is "This is where Americans do their research on Space. In addition to all computers and lab gadgets, you can find a couple of objects here which are useful during our game. Let's explore the room.".
The description of r_1 is "[US LAB part 0]".

south of r_1 and north of r_3 is a door called d_1.
north of r_1 and south of r_0 is a door called d_0.
The r_2 is mapped east of r_1.
The internal name of r_3 is "Russian Module".
The printed name of r_3 is "-= Russian Module =-".
The Russian Module part 0 is some text that varies. The Russian Module part 0 is "The Russian module is a typical space lab that you can expect, filled with a lot of processing machines, test equipments and space drive cars, in fact for repair and test. Since it is located at the center of International Space Station, it is also important room for everyone. There are many other objects here and there belongs to other astronauts, probably that's why here looks a bit messy. There are some stuffs here you should pick, obviously if you can find them among all this mess.".
The description of r_3 is "[Russian Module part 0]".

west of r_3 and east of r_5 is a door called d_2.
north of r_3 and south of r_1 is a door called d_1.
The r_4 is mapped east of r_3.
The internal name of r_5 is "Control Module".
The printed name of r_5 is "-= Control Module =-".
The Control Module part 0 is some text that varies. The Control Module part 0 is "This is the heart of this spaceship! Wow ... look around, all the monitors and panels. It is like you can control everything from here; more interestingly, you can communicate with people on the Earth. There are also super important objects kept in this room. Let's find them.".
The description of r_5 is "[Control Module part 0]".

east of r_5 and west of r_3 is a door called d_2.
The internal name of r_4 is "Lounge Module".
The printed name of r_4 is "-= Lounge Module =-".
The Lounge Module part 0 is some text that varies. The Lounge Module part 0 is "This lounge is very quiet room with a big round window to the space. Wow, you can look to our beloved Earth from this window. This room is the place that you can stay here for hours and just get relax. This room also contains some other stuff, let's explore what they are ...".
The description of r_4 is "[Lounge Module part 0]".

The r_3 is mapped west of r_4.
south of r_4 and north of r_6 is a door called d_3.
The internal name of r_0 is "Sleep Station".
The printed name of r_0 is "-= Sleep Station =-".
The Sleep Station part 0 is some text that varies. The Sleep Station part 0 is "This is a typical bedroom in spaceship; here,  it is called sleep station. It is small but comfortable to take a good rest after a day full of missions. However, today your mission will start from here. Wait to be notified by a message. So, you should find that message first. BTW, don't forget that when the Hatch door is open, you should already have worn your specially-designed outfit to be able to enter and stay at Hatch area; otherwise you'll die! Yes! Living in space is tough.".
The description of r_0 is "[Sleep Station part 0]".

south of r_0 and north of r_1 is a door called d_0.
The internal name of r_6 is "Hatch".
The printed name of r_6 is "-= Hatch =-".
The Hatch part 0 is some text that varies. The Hatch part 0 is "This area is like the entrance to the spaceship, so like home entrance with outer and inner doors and a place that outfits are hooked. There are only two important differences: first, if the outer door is open and you don't have outfit on you, you are dead!! No joke here! So make sure that you open the door after wearing those cloths. Second, the door nob to open the door is not neither on the door nor in this room. You should open the external door from Russian Module! woooh so much of safety concerns, yeah?!".
The description of r_6 is "[Hatch part 0]".

south of r_6 and north of r_7 is a door called d_4.
north of r_6 and south of r_4 is a door called d_3.
The internal name of r_7 is "Outside".
The printed name of r_7 is "-= Outside =-".
The Outside part 0 is some text that varies. The Outside part 0 is "Here is outside the spaceship. No Oxygen, no gravity, nothing! If you are here, it means that you have the special outfit on you and you passed the medium level of the game! Congrats!".
The description of r_7 is "[Outside part 0]".

north of r_7 and south of r_6 is a door called d_4.

The b_0 are button-likes.
The b_0 are privately-named.
The c_0 and the c_1 and the c_5 and the c_6 and the c_2 and the c_4 and the c_3 are containers.
The c_0 and the c_1 and the c_5 and the c_6 and the c_2 and the c_4 and the c_3 are privately-named.
The cpu_0 are CPU-likes.
The cpu_0 are privately-named.
The d_0 and the d_1 and the d_2 and the d_3 and the d_4 are doors.
The d_0 and the d_1 and the d_2 and the d_3 and the d_4 are privately-named.
The k_0 and the k_1 and the k_2 and the k_3 and the k_4 and the k_5 and the k_6 are keys.
The k_0 and the k_1 and the k_2 and the k_3 and the k_4 and the k_5 and the k_6 are privately-named.
The l_0 are cloth-likes.
The l_0 are privately-named.
The o_0 and the o_1 and the o_2 are object-likes.
The o_0 and the o_1 and the o_2 are privately-named.
The r_2 and the r_1 and the r_3 and the r_5 and the r_4 and the r_0 and the r_6 and the r_7 are rooms.
The r_2 and the r_1 and the r_3 and the r_5 and the r_4 and the r_0 and the r_6 and the r_7 are privately-named.
The s_0 and the s_1 and the s_2 and the s_3 and the s_4 are supporters.
The s_0 and the s_1 and the s_2 and the s_3 and the s_4 are privately-named.
The txt_0 are text-likes.
The txt_0 are privately-named.

The description of d_0 is "it's a commanding door A [if open]You can see inside it.[else if closed]You can't see inside it because the lid's in your way.[otherwise]There is a lock on it.[end if]".
The printed name of d_0 is "door A".
Understand "door A" as d_0.
Understand "door" as d_0.
Understand "A" as d_0.
The d_0 is closed.
The description of d_1 is "it's a manageable door B [if open]You can see inside it.[else if closed]You can't see inside it because the lid's in your way.[otherwise]There is a lock on it.[end if]".
The printed name of d_1 is "door B".
Understand "door B" as d_1.
Understand "door" as d_1.
Understand "B" as d_1.
The d_1 is locked.
The description of d_2 is "The door C looks imposing. [if open]You can see inside it.[else if closed]You can't see inside it because the lid's in your way.[otherwise]There is a lock on it.[end if]".
The printed name of d_2 is "door C".
Understand "door C" as d_2.
Understand "door" as d_2.
Understand "C" as d_2.
The d_2 is locked.
The description of d_3 is "it is what it is, a door D [if open]You can see inside it.[else if closed]You can't see inside it because the lid's in your way.[otherwise]There is a lock on it.[end if]".
The printed name of d_3 is "door D".
Understand "door D" as d_3.
Understand "door" as d_3.
Understand "D" as d_3.
The d_3 is locked.
The description of d_4 is "The door E looks rugged. [if open]It is open.[else if closed]It is closed.[otherwise]It is locked.[end if]".
The printed name of d_4 is "door E".
Understand "door E" as d_4.
Understand "door" as d_4.
Understand "E" as d_4.
The d_4 is locked.
The description of c_0 is "cool! You can sleep in a comfy bag.".
The printed name of c_0 is "sleeping bag".
Understand "sleeping bag" as c_0.
Understand "sleeping" as c_0.
Understand "bag" as c_0.
The c_0 is in r_0.
The c_0 is open.
The description of c_1 is "This a regular box, keeps the electronic key to open door C. But it is locked. The lock looks like a keypad, means that the key is in fact just a code! So, ... let's search around to find its key.".
The printed name of c_1 is "box A".
Understand "box A" as c_1.
Understand "box" as c_1.
Understand "A" as c_1.
The c_1 is in r_1.
The c_1 is locked.
The description of c_5 is "This box is actually a wall-mounted bag and you can put an object into it. Since we have no gravity in the space, you can't just simply leave the object in the room. The object should be hooked or inserted into a container like this bag. Well, know we know what it is!".
The printed name of c_5 is "box E".
Understand "box E" as c_5.
Understand "box" as c_5.
Understand "E" as c_5.
The c_5 is in r_4.
The c_5 is closed.
The description of c_6 is "This box is secured very much, simple box with a complex, strange keypad to enter the code! So ... it should contain extremely important items in it. Isn't it the thing you are looking for?!".
The printed name of c_6 is "secured box".
Understand "secured box" as c_6.
Understand "secured" as c_6.
Understand "box" as c_6.
The c_6 is in r_5.
The c_6 is locked.
The description of l_0 is "".
The printed name of l_0 is "outfit".
Understand "outfit" as l_0.
The l_0 is in r_6.
The l_0 is clean.
The l_0 is worn out.
The description of s_0 is "This is not a regular table. The surface is installed vertically and your objects are attached or hooked to it, why? Come on! we are in space, there is no gravity here.".
The printed name of s_0 is "vertical desk".
Understand "vertical desk" as s_0.
Understand "vertical" as s_0.
Understand "desk" as s_0.
The s_0 is in r_0.
The description of s_1 is "This is a simple table located in the middle of the room. Let's take a look at it...".
The printed name of s_1 is "table".
Understand "table" as s_1.
The s_1 is in r_2.
The description of s_2 is "this is a dark-gray chair which is developed to be used in space.".
The printed name of s_2 is "chair".
Understand "chair" as s_2.
The s_2 is in r_2.
The description of s_3 is "This is a big metal table, a messy one, there are many things on it, it is difficult to find what you want. However, there is just one item which is important for you. Try to find that item.".
The printed name of s_3 is "metal table".
Understand "metal table" as s_3.
Understand "metal" as s_3.
Understand "table" as s_3.
The s_3 is in r_3.
The description of s_4 is "This is a wall-mounted surface which different instruments are installed on this. These instruments are basically control various modules and doors in the shuttle.".
The printed name of s_4 is "wall-mounted surface".
Understand "wall-mounted surface" as s_4.
Understand "wall-mounted" as s_4.
Understand "surface" as s_4.
The s_4 is in r_3.
The description of c_2 is "This a regular box, keeps the key to open box A.".
The printed name of c_2 is "box B".
Understand "box B" as c_2.
Understand "box" as c_2.
Understand "B" as c_2.
The c_2 is closed.
The c_2 is on the s_1.
The description of b_0 is "This push button is a key-like object which opens door A.".
The printed name of b_0 is "exit push button".
Understand "exit push button" as b_0.
Understand "exit" as b_0.
Understand "push" as b_0.
Understand "button" as b_0.
The b_0 is in the c_4.
The b_0 pairs to d_4.
The b_0 is unpushed.
The description of c_4 is "The most important box here, which is in fact locked! sounds it carries important item... So, let's find its key to open it.".
The printed name of c_4 is "exit box".
Understand "exit box" as c_4.
Understand "exit" as c_4.
Understand "box" as c_4.
The c_4 is locked.
The c_4 is on the s_4.
The description of k_0 is "This key is a card key which opens door C.".
The printed name of k_0 is "electronic key 1".
Understand "electronic key 1" as k_0.
Understand "electronic" as k_0.
Understand "key" as k_0.
Understand "1" as k_0.
The k_0 is in the c_1.
The matching key of the d_1 is the k_0.
The description of k_1 is "This key is in fact a digital code which opens the box in the US Lab area. The code, in fact, is written on a piece of paper.".
The printed name of k_1 is "code key 1".
Understand "code key 1" as k_1.
Understand "code" as k_1.
Understand "key" as k_1.
Understand "1" as k_1.
The k_1 is in the c_2.
The matching key of the c_1 is the k_1.
The description of k_2 is "This key is an important key in this craft. If you want to leave the spaceship, you definitely need this key.".
The printed name of k_2 is "digital key 1".
Understand "digital key 1" as k_2.
Understand "digital" as k_2.
Understand "key" as k_2.
Understand "1" as k_2.
The k_2 is in the c_3.
The matching key of the c_6 is the k_2.
The description of c_3 is "This box is locked! sounds it carries important item... So, let's find its key to open it. Wait... strange! the lock looks like a heart!! Wait we've seen something similar to this somewhere before.".
The printed name of c_3 is "box C".
Understand "box C" as c_3.
Understand "box" as c_3.
Understand "C" as c_3.
The c_3 is locked.
The c_3 is on the s_3.
The description of k_3 is "This key is the key opens the door to the control room. Although it looks like a regular iron key, it is very special metal key! Not any other key can be like it. Make sure to keep it in safe place.".
The printed name of k_3 is "electronic key 2".
Understand "electronic key 2" as k_3.
Understand "electronic" as k_3.
Understand "key" as k_3.
Understand "2" as k_3.
The k_3 is in the c_5.
The matching key of the d_2 is the k_3.
The description of k_4 is "The digital key 2 is cold to the touch".
The printed name of k_4 is "digital key 2".
Understand "digital key 2" as k_4.
Understand "digital" as k_4.
Understand "key" as k_4.
Understand "2" as k_4.
The k_4 is in the c_6.
The matching key of the c_4 is the k_4.
The description of k_5 is "The code key 2 is cold to the touch".
The printed name of k_5 is "code key 2".
Understand "code key 2" as k_5.
Understand "code" as k_5.
Understand "key" as k_5.
Understand "2" as k_5.
The k_5 is in the c_6.
The matching key of the d_3 is the k_5.
The description of k_6 is "This key is shaped like a heart, not a normal key for a spaceship, ha ha ha...".
The printed name of k_6 is "hearty key".
Understand "hearty key" as k_6.
Understand "hearty" as k_6.
Understand "key" as k_6.
The player carries the k_6.
The matching key of the c_3 is the k_6.
The description of txt_0 is "If you open and check this book, here it is the description: 'This is a book of all secret codes to manage different actions and functions inside the International Space Station. These codes are pre-authorized by the main control room at Earth unless it is mentioned.' On the second page of the book, you can find this: 'To open the hatch door you should have both two keys in the secured box. ATTENTION: you MUST have the outfit on you, before opening the hatch. Otherwise, your life is in fatal danger.'".
The printed name of txt_0 is "Secret Codes Handbook".
Understand "Secret Codes Handbook" as txt_0.
Understand "Secret" as txt_0.
Understand "Codes" as txt_0.
Understand "Handbook" as txt_0.
The txt_0 is in the c_6.
The txt_0 is unread.
The description of cpu_0 is "This is your personal laptop which is attached to the surface of the table. You can do regular things with this, like check your emails, watch YouTube, Skype with family,etc.Since you are here, we recommend you to check your emails. New missions are posted through emails.".
The printed name of cpu_0 is "laptop".
Understand "laptop" as cpu_0.
The cpu_0 is on the s_0.
The cpu_0 is unread.
The description of o_0 is "The bunch of sticked papers is dirty.".
The printed name of o_0 is "bunch of sticked papers".
Understand "bunch of sticked papers" as o_0.
Understand "bunch" as o_0.
Understand "sticked" as o_0.
Understand "papers" as o_0.
The o_0 is on the s_3.
The description of o_1 is "The lots of hanged notebooks is modern.".
The printed name of o_1 is "lots of hanged notebooks".
Understand "lots of hanged notebooks" as o_1.
Understand "lots" as o_1.
Understand "hanged" as o_1.
Understand "notebooks" as o_1.
The o_1 is on the s_3.
The description of o_2 is "The attached bags for mechanical tools is dirty.".
The printed name of o_2 is "attached bags for mechanical tools".
Understand "attached bags for mechanical tools" as o_2.
Understand "attached" as o_2.
Understand "bags" as o_2.
Understand "for" as o_2.
Understand "mechanical" as o_2.
Understand "tools" as o_2.
The o_2 is on the s_3.


The player is in r_0.

The quest0 completed is a truth state that varies.
The quest0 completed is usually false.

Test quest0_0 with ""

Every turn:
	if quest0 completed is true:
		do nothing;
	else if The cpu_0 is read:
		increase the score by 1; [Quest completed]
		Now the quest0 completed is true;

The quest1 completed is a truth state that varies.
The quest1 completed is usually false.
Every turn:
	if quest1 completed is true:
		do nothing;
	else if The cpu_0 is unread and The d_0 is open:
		end the story; [Lost]

The quest2 completed is a truth state that varies.
The quest2 completed is usually false.

Test quest2_0 with ""

Every turn:
	if quest2 completed is true:
		do nothing;
	else if The player carries the k_0:
		increase the score by 1; [Quest completed]
		Now the quest2 completed is true;

The quest3 completed is a truth state that varies.
The quest3 completed is usually false.

Test quest3_0 with ""

Every turn:
	if quest3 completed is true:
		do nothing;
	else if The player carries the k_2:
		increase the score by 1; [Quest completed]
		Now the quest3 completed is true;

The quest4 completed is a truth state that varies.
The quest4 completed is usually false.

Test quest4_0 with ""

Every turn:
	if quest4 completed is true:
		do nothing;
	else if The b_0 is pushed and The l_0 is worn in:
		increase the score by 1; [Quest completed]
		Now the quest4 completed is true;

The quest5 completed is a truth state that varies.
The quest5 completed is usually false.
Every turn:
	if quest5 completed is true:
		do nothing;
	else if The b_0 is pushed and The l_0 is worn out:
		end the story; [Lost]

The quest6 completed is a truth state that varies.
The quest6 completed is usually false.

Test quest6_0 with ""

Every turn:
	if quest6 completed is true:
		do nothing;
	else if The player carries the k_5:
		increase the score by 1; [Quest completed]
		Now the quest6 completed is true;

The quest7 completed is a truth state that varies.
The quest7 completed is usually false.

Test quest7_0 with ""

Every turn:
	if quest7 completed is true:
		do nothing;
	else if The txt_0 is read:
		increase the score by 1; [Quest completed]
		Now the quest7 completed is true;

The quest8 completed is a truth state that varies.
The quest8 completed is usually false.

Test quest8_0 with ""

Every turn:
	if quest8 completed is true:
		do nothing;
	else if The l_0 is worn in:
		increase the score by 1; [Quest completed]
		Now the quest8 completed is true;

The quest9 completed is a truth state that varies.
The quest9 completed is usually false.

Test quest9_0 with ""

Every turn:
	if quest9 completed is true:
		do nothing;
	else if The player is in r_7:
		increase the score by 1; [Quest completed]
		Now the quest9 completed is true;

Use scoring. The maximum score is 8.
This is the simpler notify score changes rule:
	If the score is not the last notified score:
		let V be the score - the last notified score;
		say "Your score has just gone up by [V in words] ";
		if V > 1:
			say "points.";
		else:
			say "point.";
		Now the last notified score is the score;
	if score is maximum score:
		end the story finally; [Win]

The simpler notify score changes rule substitutes for the notify score changes rule.

Rule for listing nondescript items:
	stop.

Rule for printing the banner text:
	say "[fixed letter spacing]";
	say "                    ________  ________  __    __  ________        [line break]";
	say "                   |        \|        \|  \  |  \|        \       [line break]";
	say "                    \$$$$$$$$| $$$$$$$$| $$  | $$ \$$$$$$$$       [line break]";
	say "                      | $$   | $$__     \$$\/  $$   | $$          [line break]";
	say "                      | $$   | $$  \     >$$  $$    | $$          [line break]";
	say "                      | $$   | $$$$$    /  $$$$\    | $$          [line break]";
	say "                      | $$   | $$_____ |  $$ \$$\   | $$          [line break]";
	say "                      | $$   | $$     \| $$  | $$   | $$          [line break]";
	say "                       \$$    \$$$$$$$$ \$$   \$$    \$$          [line break]";
	say "              __       __   ______   _______   __        _______  [line break]";
	say "             |  \  _  |  \ /      \ |       \ |  \      |       \ [line break]";
	say "             | $$ / \ | $$|  $$$$$$\| $$$$$$$\| $$      | $$$$$$$\[line break]";
	say "             | $$/  $\| $$| $$  | $$| $$__| $$| $$      | $$  | $$[line break]";
	say "             | $$  $$$\ $$| $$  | $$| $$    $$| $$      | $$  | $$[line break]";
	say "             | $$ $$\$$\$$| $$  | $$| $$$$$$$\| $$      | $$  | $$[line break]";
	say "             | $$$$  \$$$$| $$__/ $$| $$  | $$| $$_____ | $$__/ $$[line break]";
	say "             | $$$    \$$$ \$$    $$| $$  | $$| $$     \| $$    $$[line break]";
	say "              \$$      \$$  \$$$$$$  \$$   \$$ \$$$$$$$$ \$$$$$$$ [line break]";
	say "[variable letter spacing][line break]";
	say "[objective][line break]".

Include Basic Screen Effects by Emily Short.

Rule for printing the player's obituary:
	if story has ended finally:
		center "*** The End ***";
	else:
		center "*** You lost! ***";
	say paragraph break;
	say "You scored [score] out of a possible [maximum score], in [turn count] turn(s).";
	[wait for any key;
	stop game abruptly;]
	rule succeeds.

Rule for implicitly taking something (called target):
	if target is fixed in place:
		say "The [target] is fixed in place.";
	otherwise:
		say "You need to take the [target] first.";
		set pronouns from target;
	stop.

Does the player mean doing something:
	if the noun is not nothing and the second noun is nothing and the player's command matches the text printed name of the noun:
		it is likely;
	if the noun is nothing and the second noun is not nothing and the player's command matches the text printed name of the second noun:
		it is likely;
	if the noun is not nothing and the second noun is not nothing and the player's command matches the text printed name of the noun and the player's command matches the text printed name of the second noun:
		it is very likely.  [Handle action with two arguments.]

Printing the content of the room is an activity.
Rule for printing the content of the room:
	let R be the location of the player;
	say "Room contents:[line break]";
	list the contents of R, with newlines, indented, including all contents, with extra indentation.

Printing the content of the world is an activity.
Rule for printing the content of the world:
	let L be the list of the rooms;
	say "World: [line break]";
	repeat with R running through L:
		say "  [the internal name of R][line break]";
	repeat with R running through L:
		say "[the internal name of R]:[line break]";
		if the list of things in R is empty:
			say "  nothing[line break]";
		otherwise:
			list the contents of R, with newlines, indented, including all contents, with extra indentation.

Printing the content of the inventory is an activity.
Rule for printing the content of the inventory:
	say "Inventory:[line break]";
	list the contents of the player, with newlines, indented, giving inventory information, including all contents, with extra indentation.

Printing the content of nowhere is an activity.
Rule for printing the content of nowhere:
	say "Nowhere:[line break]";
	let L be the list of the off-stage things;
	repeat with thing running through L:
		say "  [thing][line break]";

Printing the things on the floor is an activity.
Rule for printing the things on the floor:
	let R be the location of the player;
	let L be the list of things in R;
	remove yourself from L;
	remove the list of containers from L;
	remove the list of supporters from L;
	remove the list of doors from L;
	if the number of entries in L is greater than 0:
		say "There is [L with indefinite articles] on the floor.";

After printing the name of something (called target) while
printing the content of the room
or printing the content of the world
or printing the content of the inventory
or printing the content of nowhere:
	follow the property-aggregation rules for the target.

The property-aggregation rules are an object-based rulebook.
The property-aggregation rulebook has a list of text called the tagline.

[At the moment, we only support "open/unlocked", "closed/unlocked" and "closed/locked" for doors and containers.]
[A first property-aggregation rule for an openable open thing (this is the mention open openables rule):
	add "open" to the tagline.

A property-aggregation rule for an openable closed thing (this is the mention closed openables rule):
	add "closed" to the tagline.

A property-aggregation rule for an lockable unlocked thing (this is the mention unlocked lockable rule):
	add "unlocked" to the tagline.

A property-aggregation rule for an lockable locked thing (this is the mention locked lockable rule):
	add "locked" to the tagline.]

A first property-aggregation rule for an openable lockable open unlocked thing (this is the mention open openables rule):
	add "open" to the tagline.

A property-aggregation rule for an openable lockable closed unlocked thing (this is the mention closed openables rule):
	add "closed" to the tagline.

A property-aggregation rule for an openable lockable closed locked thing (this is the mention locked openables rule):
	add "locked" to the tagline.

A property-aggregation rule for a lockable thing (called the lockable thing) (this is the mention matching key of lockable rule):
	let X be the matching key of the lockable thing;
	if X is not nothing:
		add "match [X]" to the tagline.

A property-aggregation rule for an edible off-stage thing (this is the mention eaten edible rule):
	add "eaten" to the tagline.

The last property-aggregation rule (this is the print aggregated properties rule):
	if the number of entries in the tagline is greater than 0:
		say " ([tagline])";
		rule succeeds;
	rule fails;


An objective is some text that varies. The objective is "".
Printing the objective is an action applying to nothing.
Carry out printing the objective:
	say "[objective]".

Understand "goal" as printing the objective.

The taking action has an object called previous locale (matched as "from").

Setting action variables for taking:
	now previous locale is the holder of the noun.

Report taking something from the location:
	say "You pick up [the noun] from the ground." instead.

Report taking something:
	say "You take [the noun] from [the previous locale]." instead.

Report dropping something:
	say "You drop [the noun] on the ground." instead.

The print state option is a truth state that varies.
The print state option is usually false.

Turning on the print state option is an action applying to nothing.
Carry out turning on the print state option:
	Now the print state option is true.

Turning off the print state option is an action applying to nothing.
Carry out turning off the print state option:
	Now the print state option is false.

Printing the state is an activity.
Rule for printing the state:
	let R be the location of the player;
	say "Room: [line break] [the internal name of R][line break]";
	[say "[line break]";
	carry out the printing the content of the room activity;]
	say "[line break]";
	carry out the printing the content of the world activity;
	say "[line break]";
	carry out the printing the content of the inventory activity;
	say "[line break]";
	carry out the printing the content of nowhere activity;
	say "[line break]".

Printing the entire state is an action applying to nothing.
Carry out printing the entire state:
	say "-=STATE START=-[line break]";
	carry out the printing the state activity;
	say "[line break]Score:[line break] [score]/[maximum score][line break]";
	say "[line break]Objective:[line break] [objective][line break]";
	say "[line break]Inventory description:[line break]";
	say "  You are carrying: [a list of things carried by the player].[line break]";
	say "[line break]Room description:[line break]";
	try looking;
	say "[line break]-=STATE STOP=-";

Every turn:
	if extra description command option is true:
		say "<description>";
		try looking;
		say "</description>";
	if extra inventory command option is true:
		say "<inventory>";
		try taking inventory;
		say "</inventory>";
	if extra score command option is true:
		say "<score>[line break][score][line break]</score>";
	if print state option is true:
		try printing the entire state;

When play ends:
	if print state option is true:
		try printing the entire state;

After looking:
	carry out the printing the things on the floor activity.

Understand "print_state" as printing the entire state.
Understand "enable print state option" as turning on the print state option.
Understand "disable print state option" as turning off the print state option.

Before going through a closed door (called the blocking door):
	say "You have to open the [blocking door] first.";
	stop.

Before opening a locked door (called the locked door):
	let X be the matching key of the locked door;
	if X is nothing:
		say "The [locked door] is welded shut.";
	otherwise:
		say "You have to unlock the [locked door] with the [X] first.";
	stop.

Before opening a locked container (called the locked container):
	let X be the matching key of the locked container;
	if X is nothing:
		say "The [locked container] is welded shut.";
	otherwise:
		say "You have to unlock the [locked container] with the [X] first.";
	stop.

Displaying help message is an action applying to nothing.
Carry out displaying help message:
	say "[fixed letter spacing]Available commands:[line break]";
	say "  look:                describe the current room[line break]";
	say "  goal:                print the goal of this game[line break]";
	say "  inventory:           print player's inventory[line break]";
	say "  go <dir>:            move the player north, east, south or west[line break]";
	say "  examine ...:         examine something more closely[line break]";
	say "  eat ...:             eat edible food[line break]";
	say "  open ...:            open a door or a container[line break]";
	say "  close ...:           close a door or a container[line break]";
	say "  drop ...:            drop an object on the floor[line break]";
	say "  take ...:            take an object that is on the floor[line break]";
	say "  put ... on ...:      place an object on a supporter[line break]";
	say "  take ... from ...:   take an object from a container or a supporter[line break]";
	say "  insert ... into ...: place an object into a container[line break]";
	say "  lock ... with ...:   lock a door or a container with a key[line break]";
	say "  unlock ... with ...: unlock a door or a container with a key[line break]";

Understand "help" as displaying help message.

Taking all is an action applying to nothing.
Check taking all:
	say "You have to be more specific!";
	rule fails.

Understand "take all" as taking all.
Understand "get all" as taking all.
Understand "pick up all" as taking all.

Understand "take each" as taking all.
Understand "get each" as taking all.
Understand "pick up each" as taking all.

Understand "take everything" as taking all.
Understand "get everything" as taking all.
Understand "pick up everything" as taking all.

The extra description command option is a truth state that varies.
The extra description command option is usually false.

Turning on the extra description command option is an action applying to nothing.
Carry out turning on the extra description command option:
	Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
	Now the extra description command option is true.

Understand "tw-extra-infos description" as turning on the extra description command option.

The extra inventory command option is a truth state that varies.
The extra inventory command option is usually false.

Turning on the extra inventory command option is an action applying to nothing.
Carry out turning on the extra inventory command option:
	Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
	Now the extra inventory command option is true.

Understand "tw-extra-infos inventory" as turning on the extra inventory command option.

The extra score command option is a truth state that varies.
The extra score command option is usually false.

Turning on the extra score command option is an action applying to nothing.
Carry out turning on the extra score command option:
	Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
	Now the extra score command option is true.

Understand "tw-extra-infos score" as turning on the extra score command option.

To trace the actions:
	(- trace_actions = 1; -).

Tracing the actions is an action applying to nothing.
Carry out tracing the actions:
	Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
	trace the actions;

Understand "tw-trace-actions" as tracing the actions.

The restrict commands option is a truth state that varies.
The restrict commands option is usually false.

Turning on the restrict commands option is an action applying to nothing.
Carry out turning on the restrict commands option:
	Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
	Now the restrict commands option is true.

Understand "restrict commands" as turning on the restrict commands option.

The taking allowed flag is a truth state that varies.
The taking allowed flag is usually false.

Before removing something from something:
	now the taking allowed flag is true.

After removing something from something:
	now the taking allowed flag is false.

Before taking a thing (called the object) when the object is on a supporter (called the supporter):
	if the restrict commands option is true and taking allowed flag is false:
		say "Can't see any [object] on the floor! Try taking the [object] from the [supporter] instead.";
		rule fails.

Before of taking a thing (called the object) when the object is in a container (called the container):
	if the restrict commands option is true and taking allowed flag is false:
		say "Can't see any [object] on the floor! Try taking the [object] from the [container] instead.";
		rule fails.

Understand "take [something]" as removing it from.

Rule for supplying a missing second noun while removing:
	if restrict commands option is false and noun is on a supporter (called the supporter):
		now the second noun is the supporter;
	else if restrict commands option is false and noun is in a container (called the container):
		now the second noun is the container;
	else:
		try taking the noun;
		say ""; [Needed to avoid printing a default message.]

The version number is always 1.

Reporting the version number is an action applying to nothing.
Carry out reporting the version number:
	Decrease turn count by 1;  [Internal framework commands shouldn't count as a turn.]
	say "[version number]".

Understand "tw-print version" as reporting the version number.

Reporting max score is an action applying to nothing.
Carry out reporting max score:
	say "[maximum score]".

Understand "tw-print max_score" as reporting max score.

To print id of (something - thing):
	(- print {something}, "^"; -).

Printing the id of player is an action applying to nothing.
Carry out printing the id of player:
	print id of player.

Printing the id of EndOfObject is an action applying to nothing.
Carry out printing the id of EndOfObject:
	print id of EndOfObject.

Understand "tw-print player id" as printing the id of player.
Understand "tw-print EndOfObject id" as printing the id of EndOfObject.

There is a EndOfObject.

