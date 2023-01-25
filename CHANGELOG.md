# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog 1.0.0*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Semantic Versioning 2.0.0*](https://semver.org/).

The **first number** is the major version (API changes, breaking changes)
The **second number** is the minor version (new features)
The **third number** is the patch version (bug fixes)

<!-- changelog follows -->

## [Unreleased]

### Added

- `find`: Search for commands by name or description.

## [0.1.0](https://github.com/pederhan/harbor-cli/tree/harbor-cli-v0.1.0)

### Changed

- Update command semantics. See [#25](https://github.com/pederhan/harbor-cli/pull/25) and the [docs](https://pederhan.github.io/harbor-cli/usage/terminology/#actions-terminology).
- Type of `str` parameters that take `"true"` and `"false"` have been changed to `bool`.
  - Bool parameters for API commands now take the args `True`/`true`/`1` and `False`/`false`/`0`. Global options that override config commands are still flags in the form `--foo/--no-foo`.
  - We use the validators defined on the models from `harborapi` to automatically convert these values to the strings `"true"`/`"false"` under the hood.

### Fixed

- Some commands were missing custom text for their spinner.

### Removed

- All `update --replace` parameters. Updates are now partial updates only.

## [0.0.1](https://github.com/pederhan/harbor-cli/tree/harbor-cli-v0.0.1) - 2023-xx-yy

### Added

- Initial release.

<!-- ### Changed -->
<!-- ### Fixed -->
