# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog 1.0.0*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Semantic Versioning 2.0.0*](https://semver.org/).

The **first number** is the major version (API changes, breaking changes)
The **second number** is the minor version (new features)
The **third number** is the patch version (bug fixes)

<!-- changelog follows -->

## [Unreleased]

### Added

- "limited guest" role for the relevant `project member` commands.


### Changed

- Artifact digests are now always displayed in the short format in tables to limit the width of the table.
- `project member` commands now take a username or ID instead of a project member ID.
  - Affected commands:
    - `project member update-role`
    - `project member remove`
  - This is more consistent with the rest of application, but less consistent with the API. In most cases, we will not know the project member ID for a given user, so this change makes it easier to use the CLI to manage project members.
- Application now uses Pydantic V2 internally, which allows us to leverage the newest version of the API library ([harborapi](https://github.com/pederhan/harborapi/))

## [0.1.0](https://github.com/pederhan/harbor-cli/tree/harbor-cli-v0.0.1) - 2023-12-06

### Added

- Initial release.

<!-- ### Changed -->
<!-- ### Fixed -->
