# harbor-cli

<!-- [![PyPI - Version](https://img.shields.io/pypi/v/harbor-cli.svg)](https://pypi.org/project/harbor-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/harbor-cli.svg)](https://pypi.org/project/harbor-cli) -->

-----

**NOTE**: This project is still in early development, and most functionality, such as CLI options and configuration file format, is subject to change. Prior to version 1.0.0, breaking changes may be introduced in minor version updates.

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

<!-- ```console
pip install harbor-cli
``` -->

The name `harbor-cli` is in the process of being taken over on PyPI.

In the meantime, you can install the package from GitHub:

```
pip install git+https://github.com/pederhan/harbor-cli
```

## Usage

```
harbor --help
```

```
 Usage: harbor [OPTIONS] COMMAND [ARGS]...

 Harbor CLI

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config              -c      PATH                             Path to config file. [default: None]                                                                                │
│ --url                 -u      TEXT                             Harbor URL. [default: None]                                                                                         │
│ --username            -U      TEXT                             Harbor username. [default: None]                                                                                    │
│ --harbor-secret               TEXT                             [default: None]                                                                                                     │
│ --credentials         -C      TEXT                             Harbor basic access credentials (base64). [default: None]                                                           │
│ --credentials-file    -F      PATH                             Harbor basic access credentials file. [default: None]                                                               │
│ --table-description                                            Include field descriptions in tables. Only affects tables.                                                          │
│ --table-max-depth             INTEGER                          Maximum depth to print nested objects. Only affects tables. [default: None]                                         │
│ --format              -f      [table|json|jsonschema]          Output format. [default: table]                                                                                     │
│ --output              -o      PATH                             Output file, by default None, which means output to stdout. If the file already exists, it will be overwritten.     │
│                                                                [default: None]                                                                                                     │
│ --no-overwrite                                                 Do not overwrite the output file if it already exists.                                                              │
│ --verbose             -v                                       Enable verbose output.                                                                                              │
│ --with-stdout                                                  Output to stdout in addition to the specified output file, if any. Has no effect if no output file is specified.    │
│ --install-completion          [bash|zsh|fish|powershell|pwsh]  Install completion for the specified shell. [default: None]                                                         │
│ --show-completion             [bash|zsh|fish|powershell|pwsh]  Show completion for the specified shell, to copy it or customize the installation. [default: None]                  │
│ --help                                                         Show this message and exit.                                                                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ artifact                                       Manage artifacts.                                                                                                                   │
│ auditlog                                       System information                                                                                                                  │
│ config                                         Manage Harbor configuration.                                                                                                        │
│ cve-allowlist                                  Manage the system-wide CVE allowlist.                                                                                               │
│ gc                                             Garbage Collection scheduling and information                                                                                       │
│ init                                           Initialize Harbor CLI.                                                                                                              │
│ project                                        Manage projects.                                                                                                                    │
│ registry                                       Registry management                                                                                                                 │
│ sample-config                                  Print a sample config file to stdout.                                                                                               │
│ scan                                           Scanning of individual artifacts.                                                                                                   │
│ scan-all                                       Scanning of all artifacts.                                                                                                          │
│ scanner                                        Manage scanners.                                                                                                                    │
│ system                                         System information                                                                                                                  │
│ user                                           Manage users.                                                                                                                       │
│ vulnerabilities                                List vulnerabilities for an artifact.                                                                                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


### Terminology

Most commands are structured in the following way:

```
harbor [GLOBAL OPTIONS] COMMAND [SUBCOMMAND, SUBSUBCOMMAND, ...] [ARGS] [COMMAND OPTIONS]
```

#### `GLOBAL OPTIONS`

Global options are options that apply to all commands. They must be specified before the command. Examples of this are `--config`, `--url`, `--username`, etc. See the output of `harbor --help` above for a full list of global options.

#### `COMMAND`

Command is a resource such as `project`, `repository`, `artifact`, etc.

#### `SUBCOMMAND`, `SUBSUBCOMMAND`, etc.

Certain commands have subcommands, and these subcommands can have their own set of subcommands, etc.

An example of this is `project metadata field set`, which can be decomposed into the following:

* `COMMAND`: `project`
* `SUBCOMMAND`: `metadata`
* `SUBSUBCOMMAND`: `field`
* `SUBSUBSUBCOMMAND`: `set`

The final subcommand is the "action" to perform on the resource, such as `create`, `delete`, `list`, etc.

Actions use this terminology:

* `get` - Get a resource
* `create` - Create a resource
* `delete` - Delete a resource
* `list` - List resources (optionally filtered by a query)
* `update` - Perform a (partial) update of a resource.
  * The default behavior is similar to a PATCH request. Performs a partial update with only the given parameters (corresponding to the resource's fields) being updated on the resource.
  * **FLAG** `--replace`:  Replace the existing resource with a new resource using the provided data. Similar to a PUT request.
* `set` - Set the value of a specific field on a resource.
  * Used for setting single values, such as setting default project scanner.
* `add` - Add a value or reference to a resource to a resource
  * Used when multiple values can be added to a resource field, such as adding labels to artifacts.
* `start` - Start a job (scan, replication, etc.)
* `stop` - Stop a job
* `info` - Get information about an immutable resource
  * Used for getting information about a resource that cannot be updated by users, such as
  getting information about the system status.

#### `ARGS`

The args for a command is usually the name or ID of a resource. For example, `harbor project list` lists all projects, while `harbor project get my-project` gets the project with the name `my-project`.

#### `COMMAND OPTIONS`

Command options are options that apply to a command action. For example, `harbor project create` has an option `--public` that can be used to create a public project.

### Commands

The following commands (and their subcommands) are available:


<details>
<summary>Expand</summary>

```
artifact
  accessories
  buildhistory
  copy
  delete
  get
  label
    add
    delete
  list
  tag
    create
    delete
    list
  vulnerabilities
auditlog
  list
config
  get
  update
cve-allowlist
  clear
  get
  update
gc
  job
  jobs
  log
  schedule
    create
    get
    update
init
project
  create
  delete
  exists
  get
  list
  logs
  metadata
    field
      delete
      get
      set
    get
    set
  scanner
    candidates
    get
    set
  summary
  update
registry
  adapters
  create
  delete
  get
  list
  providers
  status
  update
sample-config
scan
  log
  start
  stop
scan-all
  metrics
  schedule
    create
    get
    update
  stop
scanner
  create
  default
  delete
  get
  list
  update
system
  health
  info
  ping
  volumes
user
  create
  delete
  get
  get-current
  get-current-permissions
  list
  search
  set-admin
  set-cli-secret
  set-password
  unset-admin
  update
vulnerabilities
```
</details>


## License

`harbor-cli` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
