
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
    * Prompts for confirmation unless `--force` is specified.
* `list` - List resources.
    * Most of these commands expose the options `--query`, `--sort`, `--limit`, `--page` and `--page-size` to filter and limit the output.
    * Each command may have its own set of options for more granular filtering of the resources such as `--tag`, `--architecture`, etc., which is syntactic sugar for the `--query` option.
    * See [harborapi docs](https://pederhan.github.io/harborapi/usage/methods/read/#query) for more information about the different parameters that can be used to filter the resources.
* `update` - Update a resource.
    * The default behavior is similar to a PATCH request. Performs a partial update with only the given parameters (corresponding to the resource's fields) being updated on the resource.
    * The CLI diverges from the API spec here, since the spec only defines PUT operations (which replaces a given resource with a new resource definition). To improve the ergonomics of the interface for users, the CLI first retrieves the existing resource and only replaces the fields the user wants to update.
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

The args for a command is usually the name or ID of a resource.

```
harbor project get my-project
```

The command specifies `my-project` as the argument for the `get` action on the `project` resource.

Certain commands accept either a name or ID as arguments. Prefix IDs with `id:` to specify that the argument is an ID. Check the relevant command's help text for more information.

## `COMMAND OPTIONS`

Command options are options that apply to a command.

```
harbor project create my-project --public
```
The command above has a `--public` option that can be used to create a public project.

### Multiple values

Certain options accept multiple values. These can be specified as a comma-separated list:

```
harbor artifact list --project library,my-project
```

Or by using the relevant option multiple times:

```
harbor artifact list --project library --project my-project
```
