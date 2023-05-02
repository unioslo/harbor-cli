
# Terminology

Commands invocation is structured as follows:

```
harbor [GLOBAL OPTIONS] COMMAND [SUBCOMMAND, SUBSUBCOMMAND, ...] [ARGS] [COMMAND OPTIONS]
```

## `GLOBAL OPTIONS`

Global options are options that apply to all commands. They must be specified before the command. Examples of this are `--config`, `--url`, `--username`, etc.

See the output of `harbor --help` for a full list of global options.

## `COMMAND`

Command is a resource such as `project`, `repository`, `artifact`, etc.

## `SUBCOMMAND`, `SUBSUBCOMMAND`, etc.

Certain commands have subcommands, and these subcommands can have their own set of subcommands, etc.

An example of this is the commmand:

```
project metadata field set
```

Which can be decomposed into the following:

* `COMMAND`: `project`
* `SUBCOMMAND`: `metadata`
* `SUBSUBCOMMAND`: `field`
* `SUBSUBSUBCOMMAND`: `set`

The final subcommand is the _action_ to perform on the resource, such as `create`, `delete`, `list`, etc.

### Actions terminology

* `get` - Get a resource
* `create` - Create a resource
* `delete` - Delete a resource
    * Prompts for confirmation unless `--force` is specified. This behavior can be disabled in the configuration file under [`general.confirm_deletion`](../../configuration/config-file/#generalconfirm_deletion).

* `list` - List resources.
    * Most of these commands expose the options `--query`, `--sort`, `--limit`, `--page` and `--page-size` to filter and limit the output.
    * Each command may have its own set of options for more granular filtering of the resources such as `--tag`, `--architecture`. Some of this behavior can be achieved with `--query` as well.
    * See [harborapi `--query` docs](https://pederhan.github.io/harborapi/usage/methods/read/#query) for more information about the different parameters that can be used to filter the resources using `--query`.
    * See [harborapi `--sort` docs](https://pederhan.github.io/harborapi/usage/methods/read/#sort) for information on how to use the `--sort` parameter.
* `update` - Update a resource.
    * The behavior of these commands mimic a PATCH request. A `update` command performs a partial update to an existing resource replacing a subset of the resource's fields with new values.
    * Parameter names attempt to be 1:1 with the resource's field names. I.e. `project update --public trueAny divergences are specified in the relevant command's help text.
    * The CLI fetches the existing resource first then replaces the given fields with the new values.[^1]
* `set` - Set the value of a specific field on a resource.
    * Used for setting single values, such as setting default project scanner.
* `add` - Add a value or reference to a resource to a resource
    * Used when multiple values can be added to a resource field, such as adding labels to artifacts.
* `start` - Start a job (scan, replication, etc.)
* `stop` - Stop a job
* `info` - Get information about an immutable resource
    * Used for getting information about a resource that cannot be updated by users, such as
    getting information about the system status.

## `ARGS`

The args for a command is usually one or more names or IDs identifying a resource. For example:

```
harbor project get my-project
```

The command specifies `my-project` as the argument for the `get` action on the `project` resource.

Certain commands accept either a name or ID as arguments. Prefix IDs with `id:` to specify that the argument is an ID. Check the relevant command's documentation for more information.

## `COMMAND OPTIONS`

Command options are options that apply to a command.

```
harbor project create my-project --public true
```
The [`project create`](../../commands/project/#project-create) command has a `--public` option that can be used to create a public project.



[^1]: The endpoints themselves are `PUT` endpoints in the Harbor API but they use `PATCH` semantics (i.e. partial updates). Until this is codified as intended behavior by Harbor, we will continue to fetch the existing resource first and then replace the given fields with the new values before sending back the updated resource to the server.
