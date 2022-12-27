# Usage

The application consists of several top-level commands pertaining to specific Harbor resources, such as `project`, `repository`, `artifact`, etc. Each of these commands have subcommands that can be used to perform actions on the resource, such as `create`, `delete`, `list`, etc.

The global options listed below must be specified before the command. Examples of this are `--config`, `--url`, `--username`, etc.

## Global options

Most of the global options (listed below) are overrides for configuration file settings. For persistent configuration of these options, see the [configuration](../configuration.md) page.

## Help output

```
$ harbor --help
{% include "help.txt" %}
```
