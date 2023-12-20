# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog 1.0.0*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Semantic Versioning 2.0.0*](https://semver.org/).

The **first number** is the major version (API changes, breaking changes)
The **second number** is the minor version (new features)
The **third number** is the patch version (bug fixes)

<!-- changelog follows -->

## [Unreleased]

### Changed

- Automatic datetime log file naming now uses the tag `{dt}` (was `{time}`).

### Fixed

- Double printing of messages in terminal if logging wasn't properly configured.

### Deprecated

- `{time}` tag for automatic datetime log file naming. Use `{dt}` instead.
- `[cache]` section in configuration file. Caching of API responses has been removed.

### Removed

- Caching of API responses. This was a premature optimization that caused more problems than it solved. It will be re-introduced in a future release.

## [0.1.0](https://github.com/pederhan/harbor-cli/tree/harbor-cli-v0.0.1) - 2023-12-06

### Added

- Initial release.

<!-- ### Added -->
<!-- ### Changed -->
<!-- ### Deprecated -->
<!-- ### Removed -->
<!-- ### Fixed -->
<!-- ### Security -->
