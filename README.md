# TextWorld
A learning environment sandbox for training and testing reinforcement learning (RL) agents on text-based games.

## Installation

TextWorld requires __Python 3__ and only supports __Linux systems__ at the moment.

### Requirements

The following system libraries are required to install and run TextWorld:
```
sudo apt-get -y install uuid-dev libffi-dev build-essential curl xdot gcc make python3-dev
```
as well as some Python libraries that can be installed separately using
```
pip install -r requirements.txt
```

### Installing TextWorld

The easiest way to install TextWorld is via `pip`.

After cloning the repo, go inside the root folder of the project (i.e. alongside `setup.py`) and run
```
pip install .
```
If you prefer a remote installation:
```
pip install https://github.com/Microsoft/TextWorld/archive/master.zip
```
_** In any case, make sure `pip` is associated with your Python 3 installation_

### Extras
If desired, one can install one or several extra functionalities for TextWorld. To do so, install TextWorld using
```
pip install .[prompt,vis]
```
where

- `[prompt]`: enables commands autocompletion (available for generated games only). To activate it, use the `--hint` option when running the `tw-play` script, and press TAB-TAB at the prompt.
- `[vis]`: enables the game states viewer (available for generated games only). To activate it, use the `--html-render` option when running the `tw-play` script, and the current state of the game will be displayed in your browser.


## Usage

### Generating a game

TextWorld provide an easy way of generating simple text-based games via the `tw-make` script. For instance,

```
tw-make custom --world-size 5 --nb-objects 10 --quest-length 5 --output gen_games/
```
where `custom` indicates we want to customize the game using the following options: `--world-size` controls the number of rooms in the world, `--nb-objects` controls the number of objects that can be interacted with (excluding doors) and `--quest-length` controls the minimum number of commands that is required to type in order to win the game. Once done, the game will be saved in the `gen_games/` folder.


### Playing a game

To play a game, one can use the `tw-play` script. For instance, the command to play the game generated in the previous section would be

```
tw-play gen_games/simple_game.ulx
```

_* Only Z-machine's games (*.z1 through *.z8) and Glulx's games (*.ulx) are supported._


## Documentation
For more information about TextWorld, check the [documentation](https://aka.ms/textworld-docs).

## Notebooks
Check the notebooks provided with the framework to see how the framework can be used.