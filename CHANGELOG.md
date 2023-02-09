# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog 1.0.0*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Semantic Versioning 2.0.0*](https://semver.org/).

The **first number** is the major version (API changes, breaking changes)
The **second number** is the minor version (new features)
The **third number** is the patch version (bug fixes)

<!-- changelog follows -->

## [Unreleased]

### Added

- Command `find`: Search for commands by name or description.
- Command `commands`: list all available commands.
- Option: `user list --sort [id|username|name]`.
- `UserResp` compact table format (used by `user list`).

### Changed

- Global option `--format` is now case-insensitive.
- Global options `--harbor-username`, `--harbor-secret` and `--harbor-url` have been deprecated in favor of `--username`, `--secret` and `--url`.

### Fixed

- Use of Python3.10 style annotations in class definitions, causing the program to not run on Python3.9 and below.

### Removed

- JSONSchema output format. Back to the drawing board on this one. [16b4ae6](https://github.com/pederhan/harbor-cli/commit/16b4ae608dfd41ea4dc9b94df1952d35aa2fd7b2)

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
