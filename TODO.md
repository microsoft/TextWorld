# List of things to do

## Viewer
- Display the game's objective when hovering a '?'/help icon.
- Better support history, i.e. highlighting action and showing corresponding feedback.
- Add a "density map" showing region visited often.
- Add a "trace map" showing the trajectory the agent took.


## Benchmark
- Provide an option to run Treasure Hunter in `benchmark.py`.

## Game
- Support tracking multiple quests.
- Support nonlinear quests.

## GameMaker
- Remove `inventory` attribute and replace it with `player`. E.g. `M.player.add(apple)`.
- Do we really need both `GameMaker.facts` and `GameMaker.state`?
- Support defining multiple quests.

## World
- Integrate it with `GameMaker` as much as possible.

## Unit test
- Make sure we use `GameMaker` in the unit tests rather than using `textworld.generator.world`.
