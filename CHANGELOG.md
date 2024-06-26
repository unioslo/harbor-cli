# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog 1.0.0*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Semantic Versioning 2.0.0*](https://semver.org/).

The **first number** is the major version (API changes, breaking changes)
The **second number** is the minor version (new features)
The **third number** is the patch version (bug fixes)

<!-- changelog follows -->

<!-- ## Unreleased -->

## [0.3.0](https://github.com/unioslo/harbor-cli/tree/harbor-cli-v0.3.0) - 2024-06-26

### Added

- Command: `project repos` to list repositories in a project. A more intuitive way to list repositories for a project than going through `repository list`.
- `--sbom-generation` option for `project create` and `project update` commands to enable automatic SBOM generation for the project.

### Changed

- Styling of multiline help text in commands.

### Removed

- Mentions of valid values from `project {create,update}` commands.

### Fixed

- REPL closing when certain errors are raised.
- `artifact list` for artifacts with no extra attributes.

## [0.2.2](https://github.com/unioslo/harbor-cli/tree/harbor-cli-v0.2.2) - 2024-03-01

### Fixed

- Configuration option `verify_ssl` not having any effect.

## [0.2.1](https://github.com/unioslo/harbor-cli/tree/harbor-cli-v0.2.1) - 2024-02-02

### Added

- Help for MacOS users if Keychain is returning a `-25244` `errSecInvalidOwnerEdit` error.
- `self keyring` command to manage the keyring.
  - `self keyring status` to see information about the keyring used.
- `self config` command to manage the configuration file.
  - Has the same commands as `cli-config`, which is now deprecated.

### Changed

- Prompts are now printed to stderr instead of stdout for POSIX compliance.
- Newlines are now logged as spaces in the log file.

### Fixed

- Coroutines not being properly cancelled when the application exits abnormally.
- Password not being stored in keyring after user is prompted for missing authentication info.
- Repeated keyring warnings if keyring is not available.

### Deprecated

- `cli-config` command. Use `self config`

## [0.2.0](https://github.com/unioslo/harbor-cli/tree/harbor-cli-v0.2.0) - 2023-12-21

### Changed

- Automatic datetime log file naming now uses the tag `{dt}` (was `{time}`).
- Log file is now named `harbor-cli.log` by default (no longer includes datetime).
  - Automatic datetime naming is now opt-in instead of being the default.

### Deprecated

- `{time}` tag for automatic datetime log file naming. Use `{dt}` instead.
- `[cache]` section in configuration file. Caching of API responses has been removed.

### Removed

- Caching of API responses. This was a premature optimization that caused more problems than it solved. It will be re-introduced in a future release.

### Fixed

- Double printing of messages in terminal if logging wasn't properly configured.

## [0.1.0](https://github.com/unioslo/harbor-cli/tree/ca08e7e8830ff3a10e1be447b5555acd5ed672ed) - 2023-12-06

### Added

- Initial release.

<!-- ### Added -->
<!-- ### Changed -->
<!-- ### Deprecated -->
<!-- ### Removed -->
<!-- ### Fixed -->
<!-- ### Security -->
