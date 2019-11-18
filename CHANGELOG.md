# Changelog

This changelog follows the following convention [https://keepachangelog.com/en/1.0.0/](https://keepachangelog.com/en/1.0.0/).

## [1.2] - 2019-09-??

### Breaking

- `textworld.envs.wrappers.Filter` expects the environment to wrap as its first argument.
- `textworld.logic.State` now requires the `GameLogic` to be provided, so that it can know about the type hierarchy of each variable.
- `has_won` and `has_lost` of `textworld.core.EnvInfos` have been renamed `won` and `lost`.
- Moved `textworld.envs.wrappers.filter.EnvInfos` to `textworld.core.EnvInfos`.

### Removed

- `textworld.envs.FrotzEnv` (use `textworld.envs.JerichoEnv` instead)
- `textworld.envs.GitGlulxML` (use `textworld.envs.TWInform7` instead)

### Added

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

- Packaging issues that prevented installation from source on macOS (#121)
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

[Unreleased]: https://github.com/Microsoft/TextWorld/compare/1.1.0...HEAD
[1.1.0]: https://github.com/Microsoft/TextWorld/compare/1.0.1...1.1.0
[1.0.1]: https://github.com/Microsoft/TextWorld/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/Microsoft/TextWorld/tree/1.0.0
