# TextWorld
[![Build Status](https://travis-ci.org/Microsoft/TextWorld.svg?branch=master)](https://travis-ci.org/Microsoft/TextWorld) [![PyPI version](https://badge.fury.io/py/textworld.svg)](https://badge.fury.io/py/textworld)

A text-based game generator and extensible sandbox learning environment for training and testing reinforcement learning (RL) agents. Also check out aka.ms/textworld for more info about TextWorld and its creators.

## Installation

TextWorld requires __Python 3__ and only supports __Linux__ and __macOS__ systems at the moment.

### Requirements

TextWorld requires some system libraries for its native components.
On a Debian/Ubuntu-based system, these can be installed with

    sudo apt install build-essential libffi-dev python3-dev curl git

And on macOS, with

    brew install libffi curl git

### Installing TextWorld

The easiest way to install TextWorld is via [`pip`](https://pypi.org/):

    pip install textworld

Or, after cloning the repo, go inside the root folder of the project (i.e. alongside `setup.py`) and run

    pip install .

### Extras

In order to use the `take_screenshot` or `visualize` functions in `textworld.render`, you'll need to install either the [Chrome](https://sites.google.com/a/chromium.org/chromedriver/) or [Firefox](https://github.com/mozilla/geckodriver) webdriver (depending on which browser you have installed).
If you have Chrome already installed you can use the following command to install chromedriver

    pip install chromedriver_installer


## Usage

### Generating a game

TextWorld provides an easy way of generating simple text-based games via the `tw-make` script. For instance,

    tw-make custom --world-size 5 --nb-objects 10 --quest-length 5 --seed 1234 --output gen_games/

where `custom` indicates we want to customize the game using the following options: `--world-size` controls the number of rooms in the world, `--nb-objects` controls the number of objects that can be interacted with (excluding doors) and `--quest-length` controls the minimum number of commands that is required to type in order to win the game. Once done, the game `game_1234.ulx` will be saved in the `gen_games/` folder.


### Playing a game (terminal)

To play a game, one can use the `tw-play` script. For instance, the command to play the game generated in the previous section would be

    tw-play gen_games/simple_game.ulx

> **Note:** Only Z-machine's games (*.z1 through *.z8) and Glulx's games (*.ulx) are supported.

### Playing a game (Python)

Here's how you can interact with a text-based game from within Python.

```python
import textworld

env = textworld.start("gen_games/game_1234.ulx")  # Start an existing game.
agent = textworld.agents.NaiveAgent()  # Or your own `textworld.Agent` subclass.

# Collect some statistics: nb_steps, final reward.
avg_moves, avg_scores = [], []
N = 10
for no_episode in range(N):
    agent.reset(env)  # Tell the agent a new episode is starting.
    game_state = env.reset()  # Start new episode.

    reward = 0
    done = False
    for no_step in range(100):
        command = agent.act(game_state, reward, done)
        game_state, reward, done = env.step(command)

        if done:
            break

    # See https://textworld-docs.maluuba.com/textworld.html#textworld.core.GameState
    avg_moves.append(game_state.nb_moves)
    avg_scores.append(game_state.score)

env.close()
print("avg. steps: {:5.1f}; avg. score: {:4.1f} / 1.".format(sum(avg_moves)/N, sum(avg_scores)/N))
```

## Documentation
For more information about TextWorld, check the [documentation](https://aka.ms/textworld-docs).

## Notebooks
Check the [notebooks](notebooks) provided with the framework to see how the framework can be used.

## Citing TextWorld
If you use TextWorld, please cite the following BibTex:
```
@Article{cote18textworld,
  author = {Marc-Alexandre C\^ot\'e and
            \'Akos K\'ad\'ar and
            Xingdi Yuan and
            Ben Kybartas and
            Tavian Barnes and
            Emery Fine and
            James Moore and
            Matthew Hausknecht and
            Layla El Asri and
            Mahmoud Adada and
            Wendy Tay and
            Adam Trischler},
  title = {TextWorld: A Learning Environment for Text-based Games},
  journal = {CoRR},
  volume = {abs/1806.11532},
  year = {2018}
}
```

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
