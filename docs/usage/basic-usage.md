# Basics

The application consists of several top-level commands pertaining to specific Harbor resources, such as `project`, `repository`, `artifact`, etc. Each of these commands have subcommands that can be used to perform actions on the resource, such as `create`, `delete`, `list`, etc.


## Global options

Most of the global options listed in [Help output](#help-output) are overrides for configuration file settings. These options can be used to override configuration options. See [Options](./options.md) for more information about each of the options. For persistent configuration of these options, see [Configuration](/configuration/config-file).

Global options must be specified before the command to run, e.g.:

```
harbor --format json project list
```

## Help output

```
$ harbor --help
{% include "help.txt" %}
```
