# Changelog

This changelog follows the following convention [https://keepachangelog.com/en/1.0.0/](https://keepachangelog.com/en/1.0.0/).

## [1.6.0] - 2023-11-28
### Breaking
- Rename `Environment.infos` to `Environment.request_infos` [[#325](https://github.com/microsoft/TextWorld/pull/325)]
- Use importlib.resources instead of pkg_resources (not supported by Python 3.8) [[#329](https://github.com/microsoft/TextWorld/pull/329), [#332](https://github.com/microsoft/]TextWorld/pull/332)]

### Added
- Add support for Python 3.10, 3.11 and 3.12 [[#328](https://github.com/microsoft/TextWorld/pull/328)]
- `GenericEnvironment` will detect which environment to load based on the game's file extension [[#330](https://github.com/microsoft/TextWorld/pull/330)]
- Support providing custom TextWorld wrappers when registring games. [[#333](https://github.com/microsoft/TextWorld/pull/333)]
- Support negating propositions and predicates. Support creating rule from conjunctive query expression. [[#334](https://github.com/microsoft/TextWorld/pull/334)]
- Add PDDL support needed for ALFWorld [[#336](https://github.com/microsoft/TextWorld/pull/336)]

### Changed
- Switch to pytest instead of nosetest [[#327](https://github.com/microsoft/TextWorld/pull/327)]
- Avoid loading viewers unless it is really needed [[#331](https://github.com/microsoft/TextWorld/pull/331)]

## [1.5.3] - 2023-05-04
### Fixed
- Fix MacOS setup [[#311](https://github.com/microsoft/TextWorld/pull/311)]
- Fix jquery security issue [[#309](https://github.com/microsoft/TextWorld/pull/309)]

## [1.5.2] - 2022-09-16
### Fixed
- Fix security issue [[#301](https://github.com/microsoft/TextWorld/pull/301)]
- Fix requirements and Inform7 links [[#303](https://github.com/microsoft/TextWorld/pull/303)]
- Fix gym version [[#305](https://github.com/microsoft/TextWorld/pull/305)]
- Fix documentation [[#306](https://github.com/microsoft/TextWorld/pull/306)]
- Rename main branch and references to it [[#307](https://github.com/microsoft/TextWorld/pull/307)]
- Use functools.partial instead of lambda functions. It's more multiprocessing friendly. [[#294](https://github.com/microsoft/TextWorld/pull/294)]
- Wait for visualization server to be ready before connecting with Selenium. [[#294](https://github.com/microsoft/TextWorld/pull/294)]
- Use constants' type as their name instead of `None`. [[#293](https://github.com/microsoft/TextWorld/pull/293)]

## Removed

- Remove MacOS 10.14 CI. [[#294](https://github.com/microsoft/TextWorld/pull/294)]

## [1.5.1] - 2022-01-09

### Added

- Allow to provide list of seeds in `AsyncBatchEnv` and `SyncBatchEnv`. [[#290](https://github.com/microsoft/TextWorld/pull/290)]

### Fixed

- Typo in `TextworldBatchGymEnv.reset`: `self.ob` instead of `self.obs`. [[#291](https://github.com/microsoft/TextWorld/pull/291)]

## [1.5.0] - 2021-12-01

### Added

- Add optional and repeatable quests. [[#288](https://github.com/microsoft/TextWorld/pull/288)]

## [1.4.5] - 2021-10-29

### Fixed

- Update notebooks. [[#285](https://github.com/microsoft/TextWorld/pull/285)]
- Fix Azure pipelines. [[#283](https://github.com/microsoft/TextWorld/pull/283)]
- Extract description and inventory from Jericho. [[#278](https://github.com/microsoft/TextWorld/pull/278)]

## [1.4.4] - 2021-09-02

### Added

- Add win_facts and fail_facts to EnvInfos. [[#274](https://github.com/microsoft/TextWorld/pull/274)]

## [1.4.3] - 2021-06-17

### Added

- List available challenges when tw-make is called with no argument. [[#267](https://github.com/microsoft/TextWorld/pull/267)]

### Fixed

- Type inheritance for command templates in `tw-extract commands ...` was not properly handled. [[#269](https://github.com/microsoft/TextWorld/pull/269)]

## [1.4.2] - 2021-05-11

### Added

- Use `--hint` to display expert policy when playing a game with `tw-play`. [[#265](https://github.com/microsoft/TextWorld/pull/265)]
- Support policy_commands for tw-cooking games with no `--drop`. [[#261](https://github.com/microsoft/TextWorld/pull/261)]

### Fixed

- `JerichoEnv._reset` wasn't set properly in `JerichoEnv.copy()`. [[#263](https://github.com/microsoft/TextWorld/pull/263)]
- Use policy induced by the event dependency tree as `EventProgression`'s winning policy. [[#263](https://github.com/microsoft/TextWorld/pull/263)]

## [1.4.1] - 2021-05-06

### Fixed

- `tw-cooking` games with `--recipe > 1` couldn't be solved using admissible commands. [[#259](https://github.com/microsoft/TextWorld/pull/259)]

## [1.4.0] - 2020-11-13

### Added

- Add `TextWorldEnv` that support loading .json gamefile directly. [[#255](https://github.com/microsoft/TextWorld/pull/255)]
- Add `tw-view`, a script to visualize game's initial state as a graph. [[#255](https://github.com/microsoft/TextWorld/pull/255)]

### Fixed

- `tw-make` was not using the right file format when saving the game. [[#255](https://github.com/microsoft/TextWorld/pull/255)]

## [1.3.3] - 2020-11-10

### Fixed

- Understand room's names as their room's id in the Inform7 code. [[#253](https://github.com/microsoft/TextWorld/pull/253)]
- Make Inform7 events detection case-insensitive. [[#253](https://github.com/microsoft/TextWorld/pull/253)]

## Removed

- Remove Python 3.5 CI since it has now reached end-of-life. [[#253](https://github.com/microsoft/TextWorld/pull/253)]

## [1.3.2] - 2020-06-01

### Fixed

- Prevent overwriting the name of matching entities (e.g. container-key). [[#237](https://github.com/microsoft/TextWorld/pull/237)]

## [1.3.1] - 2020-04-07

### Fixed

- Use Inform7 interim version for MacOS. [[#231](https://github.com/microsoft/TextWorld/pull/231)]

## [1.3.0] - 2020-03-19

### Breaking

- In `tw-make`, can't change grammar options when generating games for TextWorld challenges. [[#216](https://github.com/microsoft/TextWorld/pull/216)]
- `GameMaker.add_random_quest` -> `GameMaker.generate_random_quests`. [[#222](https://github.com/microsoft/TextWorld/pull/222)]
- `GameMaker.add_distractors` -> `GameMaker.generate_distractors`. [[#222](https://github.com/microsoft/TextWorld/pull/222)]

### Removed

- Theme "basic1" (use "basic" instead). [[#219](https://github.com/microsoft/TextWorld/pull/219)]

### Added

- Add documentation for `tw-play`, `tw-make`, and `tw-extract`. [[#227](https://github.com/microsoft/TextWorld/pull/227)]
- Add `feedback` field to `EnvInfos`. [[#226](https://github.com/microsoft/TextWorld/pull/226)]
- Add `walkthrough` property to `Game` objects. [[#225](https://github.com/microsoft/TextWorld/pull/225)]
- Add `walkthroughs` subcommand to `tw-extract`. [[#223](https://github.com/microsoft/TextWorld/pull/223)]
- Add `commands` subcommand to `tw-extract`. [[#223](https://github.com/microsoft/TextWorld/pull/223)]
- Docker image for TextWorld: [marccote19/textworld](https://hub.docker.com/r/marccote19/textworld). [[#222](https://github.com/microsoft/TextWorld/pull/222)]
- Add `requirements-full.txt` which contains all Python dependencies for TextWorld. [[#222](https://github.com/microsoft/TextWorld/pull/222)]
- Use `TEXTWORLD_DEBUG=1` to print Inform7 events detected by TextWorld when playing a game. [[#217](https://github.com/microsoft/TextWorld/pull/217)]
- Add `ChainingOptions.allowed_types` which is complementary to `ChainingOptions.restricted_types`. [[#219](https://github.com/microsoft/TextWorld/pull/219)]
- Speed up quest generation when `ChainingOptions.create_variables==True` by fixing `r` to corresponding value in `at(P, r)`. [[#219](https://github.com/microsoft/TextWorld/pull/219)]

### Fixed

- Updated games shipped with the notebooks. [[#225](https://github.com/microsoft/TextWorld/pull/225)]
- Calling `GameOptions.seeds`, without setting a seed first, will return random seeds. [[#222](https://github.com/microsoft/TextWorld/pull/222)]
- Challenges shipped with TextWorld now contain a snapshot of the KnowledgeBase to improve reproducibility. [[#216](https://github.com/microsoft/TextWorld/pull/216)]
- Delete socket files created by `mlglk` on garbage collection. [[#215](https://github.com/microsoft/TextWorld/pull/215)]
- Issues related to tw-treasure_hunter challenge [[#85](https://github.com/microsoft/TextWorld/issues/85), [#164](https://github.com/microsoft/TextWorld/issues/164)]

## [1.2.0] - 2020-02-12

### Breaking

- `Game.main_quest` attribute has been removed. To get walkthrough commands, use `Game.metadata["walkthrough"]` instead.
- `textworld.envs.wrappers.Filter` expects the environment to wrap as its first argument.
- `textworld.logic.State` now requires the `GameLogic` to be provided, so that it can know about the type hierarchy of each variable.
- `has_won` and `has_lost` of `textworld.core.EnvInfos` have been renamed `won` and `lost`.
- Moved `textworld.envs.wrappers.filter.EnvInfos` to `textworld.core.EnvInfos`.

### Removed

- `textworld.gym.make_batch` (use `textworld.gym.register_games(batch_size=...)` instead).
- `textworld.envs.FrotzEnv` (use `textworld.envs.JerichoEnv` instead)
- `textworld.envs.GitGlulxML` (use `textworld.envs.TWInform7` instead)

### Added

- Tool to visualize game state as a graph.
- Add auto-reset option when playing batch of games.
- Z-Machine can now be played with the Gym interface.
- Set up CI with Azure Pipelines to check PEP8 and track code coverage.
- Add caching for `Signature`/`Proposition` instantiation.
- `textworld.GameMaker` constructor takes optionally a `GameOptions` instance as input.
- Support requesting list of facts and current location as additional infos.
- Added `--entity-numbering` option to `tw-make`.
- Requesting additional information for TW games compiled to Z-Machine.
- Quest tracking for TW games compiled to Z-Machine.
- Added separate wrappers for dealing with additional information and state tracking.
- The `textworld.core.Environment` constructor takes an optional `EnvInfos` object.
- Use `textworld.core.EnvInfos(moves=True)` to request the nb. of moves done so far in a game.

### Fixed

- `tw-make tw-coin_collector` was failing with option `--level {100, 200, or 300}`.
- Quest tracking was failing when an irreversible, but unneeded, action was performed.

## [1.1.1] - 2019-02-08

### Fixed

- Packaging issues that prevented installation from source on macOS [[#121](https://github.com/microsoft/TextWorld/issues/121)]
- Version numbers in documentation

## [1.1.0] - 2019-02-07

### Breaking

- Previous `tw-make` commands might generate different outcomes.

### Changed

- Force `tw-make` to respect `--quest-length`.
- Fix multiprocessing issue with `ParallelBatchEnv`.
- Make installation procedures more robust.
- Notebooks are up-to-date.

### Added

- Registration mechanism for TextWorld challenges.
- More control over quest generation with `tw-make` (e.g. `--quest-breadth`).
- Documentation about the `textworld.gym` API.

## [1.0.1] - 2019-01-07

### Changed

- Updated the versions of the Jericho and prompt_toolkit dependencies

### Removed

- Removed unused libuuid dependency

## [1.0.0] - 2018-12-07

### Added

- Initial release.

[Unreleased]: https://github.com/Microsoft/TextWorld/compare/1.6.0...HEAD
[1.6.0]: https://github.com/Microsoft/TextWorld/compare/1.5.4...1.6.0
[1.5.3]: https://github.com/Microsoft/TextWorld/compare/1.5.0...1.5.3
[1.5.0]: https://github.com/Microsoft/TextWorld/compare/1.4.4...1.5.0
[1.4.4]: https://github.com/Microsoft/TextWorld/compare/1.4.3...1.4.4
[1.4.3]: https://github.com/Microsoft/TextWorld/compare/1.4.2...1.4.3
[1.4.2]: https://github.com/Microsoft/TextWorld/compare/1.4.1...1.4.2
[1.4.1]: https://github.com/Microsoft/TextWorld/compare/1.4.0...1.4.1
[1.4.0]: https://github.com/Microsoft/TextWorld/compare/1.3.3...1.4.0
[1.3.3]: https://github.com/Microsoft/TextWorld/compare/1.3.2...1.3.3
[1.3.2]: https://github.com/Microsoft/TextWorld/compare/1.3.1...1.3.2
[1.3.1]: https://github.com/Microsoft/TextWorld/compare/1.3.0...1.3.1
[1.3.0]: https://github.com/Microsoft/TextWorld/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/Microsoft/TextWorld/compare/1.1.1...1.2.0
[1.1.1]: https://github.com/Microsoft/TextWorld/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/Microsoft/TextWorld/compare/1.0.1...1.1.0
[1.0.1]: https://github.com/Microsoft/TextWorld/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/Microsoft/TextWorld/tree/1.0.0
