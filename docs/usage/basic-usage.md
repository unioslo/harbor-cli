# Basics

The application consists of several top-level commands pertaining to specific Harbor resources, such as `project`, `repository`, `artifact`, etc. Each of these commands have subcommands that can be used to perform actions on the resource, such as `create`, `delete`, `list`, etc.

See [Actions terminology](../terminology/#actions-terminology) for more information about the semantics of the different actions.

## Command

A command is typically invoked as follows:

```
harbor project list
```

`project` is the resource type, and `list` is the action to perform on the resource, and together they form the command. Most commands are _namespaced_ in this way, where a resource type has one or more actions associated with it. Some command even have subsubcommands, such as:

```
harbor project metadata field set
```

For more information about how command names are structured, see [Terminology](../terminology).


## Arguments

Commands sometimes take one or more positional arguments:

```
artifact tag create library/hello-world:latest my-tag
```

The command [`artifact tag create`](../../commands/artifact_tag/#artifact-tag-create) takes two positional arguments:

* `library/hello-world:latest` - The artifact to tag
* `my-tag` - The name of the tag to create

These are _positional_ arguments, which means the order in which they are specified is important.

### Argument types

The expected type of an argument is specified in the command's documentation. The following types are used:

<!-- TODO: fill out this section via templating. New types may be added. -->

#### `text`

A text string. Can be any sequence of characters. Enclose in quotes if it contains spaces.

#### `integer`

A whole number without a decimal point. Unconstrained unless otherwise specified in the command's help text.

#### `boolean`

A boolean value. Can be `true`, `false`, `1`, or `0`. Case-insensitive.


!!! info
    A boolean argument is typically used for resources whose value can be `None`, `True` or `False`.

#### `choice`

A choice between a set of values. The valid values are specified in the help text for the command.


## Options

Most commands also have a number of options that can be specified. In certain cases at least one option is required, such as when updating a project with [`project update`](../../commands/project/#project-update):

```
harbor project update my-project --public false
```

Since we are updating a resource, we are expected to specify at least one field to update. In this case we set `--public` to `false`, making the project private.

### Multiple values

Certain options accept multiple values. These can be specified as a comma-separated list:

```
harbor artifact list --project library,my-project
```

Or by using the relevant option multiple times:

```
harbor artifact list --project library --project my-project
```

### Flags

Some options are flags, meaning they do not take any arguments. Flags are specified as follows:

```
harbor project list --public
```

Flags can be inverted by prefixing the flag name with `no-`:

```
harbor project list --no-public
```


!!! info
    Flags are typically used to toggle a certain behavior. For example, the `--public` flag for [`project list`](../../commands/project/#project-list) can be used to list only public projects.



## Global options

Global options are options that apply to all commands. They must be specified before the command. Examples of these are [`--config`](../options/#-config-c), [`--url`](../options/#-url-u) and [`--username`]((../options/#-username-u)).

Global options must be specified before the command to run, e.g.:

```
harbor --format json project list
```

See the [Options](./options.md) page for more information on the available global options.



## Help

For more information about a specific command, use:

```
harbor <command> --help
```

See [Commands](../commands/index.md) for more in-depth information about how to use the various commands.


## Search for commands

To search for a command based on name or description, use:

```
harbor find QUERY... [OPTIONS]
```

See [`harbor find`](../commands/find.md) for more information.


## Help output

The output of `harbor --help` shows all the available commands and command groups along with the global options:

```
$ harbor --help
{% include "help.txt" %}
```
