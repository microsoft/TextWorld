# Jericho :ghost:
**Jericho is an environment that connects learning agents with interactive fiction games.** Jericho uses [Frotz](http://frotz.sourceforge.net/) and [Ztools](http://inform-fiction.org/zmachine/ztools.html) to provide a fast, python-based interface to Z-machine games.

## Requirements
***Linux***, ***Python 3***, and basic build tools like ***gcc***.

## Install
```bash
git clone git@github.com:Microsoft/TextWorld.git
cd TextWorld/jericho
pip3 install --user .
```

## Usage
```python
from jericho import *
env = FrotzEnv("roms/zork1.z5", seed=12)
# Take an action in the environment using the step() fuction.
# The resulting text observation and game score is returned.
observation, score, done, info = env.step('open mailbox')
# Reset the game to start anew
env.reset()
# Game have different max scores
env.get_max_score()
# Saving the game is possible with save_str()
saved_game = env.save_str()
# Loading is just as easy
env.load_str(saved_game)

# Jericho supports visibilty into the game including viewing the RAM
env.get_ram()
# And the object tree
env.get_world_objects()
# As well as shortcuts for particular objects, such as the player
env.get_player_object()
# And their inventory
env.get_inventory()
# Or their location
env.get_player_location()

# It's also possible to teleport the player to a location
env.teleport_player(123)
# Or to teleport an object to the player
env.teleport_obj_to_player(164)
# Be careful with these methods as they can teleport objects that aren't meant to be moved.
# NOTE: after teleportation, need to look twice before description updates.

# Finally, to detect whether an action was recognized by the parser and changed the game state
env.step('hail taxi')
if env.world_changed():
  print('We found a valid action!')
```
