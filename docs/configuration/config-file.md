# Configuration file

This section goes over every config category in detail. It is not meant to be read from start to finish, but rather to be used as a reference when configuring the application.

## Sample configuration file

```toml
{% include "sample_config.toml" %}
```

!!! warning
    The name of the `output.JSON` table is case-sensitive. The reason this name is upper-case is due to a conflict with the built-in Pydantic `json` method. This will hopefully be fixed in a future release.


## Configuration file structure

The configuration file is structured as a [TOML](https://toml.io/en/) file. The TOML file is divided into tables, which are defined by square brackets. The tables are then divided into key-value pairs, where the key is the name of the setting, and the value is the value of the setting.

The configuration file is divided into the following tables:

- [harbor](#harbor)
- [harbor.retry](#harborretry)
- [general](#general)
- [output](#output)
- [output.table](#outputtable)
- [output.table.style](#outputtablestyle)
- [output.JSON](#outputjson)
- [repl](#repl)
- [logging](#logging)

### `harbor`

The `harbor` table contains settings related to your Harbor instance. There are 3 main ways of authenticating with Harbor:

1. Using a username and password
2. Using Base64-encoded basic access credentials (`username:password` in Base64). This is not safer than using a username and password, as it only obscures the credentials, but does not encrypt them.
3. Using a Harbor robot account with a JSON credentials file. See [Create Project Robot Accounts](https://goharbor.io/docs/2.5.0/working-with-projects/project-configuration/create-robot-accounts/) and [Create System Robot Accounts](https://goharbor.io/docs/2.2.0/administration/robot-accounts/) for more information on how to create robot accounts. Robot accounts can also be created through the API with the help of `harborapi`, as described in [this](https://pederhan.github.io/harborapi/usage/creating-system-robot/) guide.

The order in which they are specified here is also the order they are evaluated. If multiple methods are specified, the first one that is valid will be used.

----


#### `harbor.url`

Fully qualified domain name of the Harbor instance. Must include the full API path (e.g. `/api/v2.0`).
```toml

```toml
[harbor]
url = "https://demo.goharbor.io/api/v2.0"
```

----

#### `harbor.username`

The username to use when authenticating with Harbor. When `username` is specified, `secret` must also be specified.

```toml
[harbor]
username = "admin"
```

----

#### `harbor.secret`

The secret (password) to use when authentication with a username. When `secret` is specified, `username` must also be specified.

```toml
[harbor]
secret = "password"
```

----

#### `harbor.basicauth`

The Base64-encoded basic access credentials to use when authenticating with Harbor. When `basicauth` is specified, `username` and `secret` must not be specified.

```toml
[harbor]
basicauth="dXNlcm5hbWU6cGFzc3dvcmQ="
```

----

#### `harbor.credentials_file`

The path to the JSON credentials file to use when authenticating. Typically obtained when creating a Robot Account. When `credentials_file` is specified, `username` and `secret` and `basicauth` must not be specified.

```toml
[harbor]
credentials_file = "/path/to/credentials.json"
```

----
#### `harbor.validate_data`

Controls whether or not the [harborapi](https://github.com/pederhan/harborapi) library  validates the data returned by the Harbor API.  Forces the output format to `json` if `false`. Not guaranteed to work with all commands. The default is `true`.


```toml
[harbor]
validate_data = true
```

----
#### `harbor.raw_mode`

Controls whether or not the data from the API should be processed by the [harborapi](https://github.com/pederhan/harborapi) library before being returned. Overrides `harbor.validate_data`. Ignores output mode. Not guaranteed to work with all commands. The default is `false`.


```toml
[harbor]
raw_mode = false
```

----
#### `harbor.verify_ssl`

Control verification of the SSL certificate of the Harbor instance. The default is `true`.

```toml
[harbor]
verify_ssl = true
```

!!! info
    In the future, this option might be expanded to allow for more fine-grained control of the SSL verification.

----

#### `harbor.keyring`

Retrieve password from keyring. This value is automatically set by the configuration wizard. See [Authentication](../auth/) for more information. The default is `false`.

```toml
[harbor]
keyring = true
```

----

### `harbor.retry`

The `harbor.retry` table contains settings related to retrying failed HTTP requests to the Harbor API.

----

#### `harbor.retry.enabled`

Enable retrying of failed requests. By default `true`.

```toml
[harbor.retry]
enabled = true
```

----

#### `harbor.retry.max_tries`

Maximum number of times to retry failed requests. By default `5`.

```toml
[harbor.retry]
max_tries = 5
```

----

#### `harbor.retry.max_time`

Maximum time in seconds to retry failed requests. By default `10`.

```toml
[harbor.retry]
max_time = 10
```

----

### `general`

The `general` table contains general CLI settings that don't fit into any other categories.

----

#### `general.confirm_enumeration`

Show a confirmation prompt when enumerating resources (e.g. `harbor auditlog list`) without a limit and/or query. The default is `true`.

Only affects the following commands:

<!-- TODO: generate this list dynamically somehow -->

* `artifact list`
* `auditlog list`
* `replication list`
* `gc jobs`
* `project logs`

```toml
[general]
confirm_enumeration = true
```

----

#### `general.confirm_deletion`

Whether or not to show a confirmation prompt when deleting resources unless `--force` is passed in. The default is `true`.

```toml
[general]
confirm_deletion = true
```

#### `general.warnings`

Show warning messages in terminal. Warnings are always logged regardless of this option. The default is `true`.

```toml
[general]
warnings = true
```

----

### `output`

The `output` table contains settings related to the output of Harbor CLI.

----

#### `output.format`

Harbor CLI currently supports {{ formats | length }} different output formats:

{% for format in formats %}
- `{{ format }}`
{% endfor %}

See [Formats](formats.md) for more information on the different output formats.

```toml
[output]
format = "table"
```

----

#### `output.paging`

Show the output in a pager (less, etc.). The default is `false`.

```toml
[output]
paging = false
```

----

#### `output.pager`

The pager to use. No value means that the default Rich pager will be used. Has no effect if `output.paging` is `false`. Equivalent to setting the `MANPAGER` and/or `PAGER` environment variables.

Can be used to redirect output to any application you want, not just pagers, for example: `output.pager = "code -"` to redirect printing of results to VS Code.

```toml
[output]
pager = "less -r" # omit to use default
```

----

### `output.table`

The `output.table` table contains settings related to the `table` output format.

See [Formats: Table](formats.md#table-table) for more information.

----

#### `output.table.description`

Whether or not to include the descriptions of each value in the output tables. Mutually exclusive with [`output.table.compact`](#outputtablecompact). The default is `false`.

```toml
[output.table]
description = false
```

----

#### `output.table.compact`

Whether or not to use compact output tables. Mutually exclusive with [`output.table.description`](#outputtabledescription). The default is `True`. Takes precedence over [`output.table.description`](#outputtabledescription) if both are enabled.

```toml
[output.table]
compact = false
```

See [Formats: Compact Tables](formats.md#compact-tables) for more information.

----

### `output.table.style`

Configuration for styling of Rich tables. Largely follows style options of [Rich tables](https://rich.readthedocs.io/en/stable/tables.html#table-options). Styles are specified as [Rich styles](https://rich.readthedocs.io/en/stable/style.html#styles). A list of colors can be found [here](https://rich.readthedocs.io/en/stable/appendix/colors.html).


----

#### `output.table.style.title`

Style of table titles.

```toml
[output.table.style]
title = "bold green"
```

----

#### `output.table.style.header`

Style of table headers.

```toml
[output.table.style]
header = "bold green"
```

----

#### `output.table.style.rows`

Style of table rows. Can be a list of two different styles, one for even rows and one for odd rows, or a string specifying a single style for all rows.

To style alternating rows only, provide a list where one of the elements is an empty string. First element for odd rows, second element for even rows.


```toml
[output.table.style]
rows = "black on white"
# or (same as above)
rows = ["black on white", "white on black"]
# or (odd rows only)
rows = ["black on white", ""]
# or (even rows only)
rows = ["", "black on white"]
```

----

#### `output.table.style.border`

Styling of border characters.

```toml
[output.table.style]
border = "bold green"
```

----

#### `output.table.style.footer`

Styling of table footers.

```toml
[output.table.style]
footer = "bold green"
```

----

#### `output.table.style.caption`

Styling of table captions.

```toml
[output.table.style]
caption = "bold green"
```

----

#### `output.table.style.expand`

Expand table to fill terminal width.


```toml
[output.table.style]
expand = true
```

----

#### `output.table.style.show_header`

Display a header over each table. Typically states the type of resource being displayed.

```toml
[output.table.style]
show_header = true
```

----

#### `output.table.style.bool_emoji`

Render booleans as emojis. The default is `false`.

```toml
[output.table.style]
bool_emoji = false
```

### `output.JSON`

The `output.JSON` table contains settings related to the `JSON` output format.

See [Formats: JSON](formats.md#json-json) for more information.

----

#### `output.JSON.indent`

Number of spaces to use for each level of indentation. The default is `2`.


```toml
[output.JSON]
indent = 2
```

----

#### `output.JSON.sort_keys`

Sort JSON keys before printing. The default is `false`.

```toml
[output.JSON]
sort_keys = false
```

----

### `repl`

The `repl` table contains settings related to the REPL.

----

#### `repl.history`

Whether or not to enable command history in the REPL. The default is `true`.


```toml
[repl]
history = true
```

----

#### `repl.history_file`

Custom path for the command history file. The default path is based on OS, and is determined by [platformdirs.user_data_dir](https://pypi.org/project/platformdirs/).


```toml
[repl]
history_file = "/path/to/history_file"
```

----

### `logging`

The `logging` table contains settings related to configuring logging. Logs are exclusively written to a log file and never displayed in the terminal. The default log directory is determined by [platformdirs.user_log_dir](https://pypi.org/project/platformdirs/).

----

#### `logging.enabled`

Whether or not to enable logging. The default is `true`.

```toml
[logging]
enabled = true
```


----

#### `logging.level`

The logging level to use. The default is `WARNING`. The available logging levels are:
`
- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

```toml
[logging]
level = "WARNING"
```

#### `logging.directory`

Custom directory to store logs in. Defaults to application log directory determined by [platformdirs.user_log_dir](https://pypi.org/project/platformdirs/).

```toml
[logging]
directory = "/path/to/logdir"
```

----

#### `logging.filename`

Filename to use for log files. If `{dt}` is included in the filename, it will be replaced with the current time. The default is `harbor_cli.log` (no automatic date and/or time).

```toml
[logging]
filename = "harbor_cli_{dt}.log"
```

----

#### `logging.datetime_format`

The datetime format that is used when automatically timing log files. Defaults to `"%Y-%m-%d"`. See [Python's strftime documentation](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) for more information on how to format the time.

```toml
[logging]
datetime_format = "%Y-%m-%d"
```

----

#### `logging.retention`

Number of days to retain log files. Defaults to 30 days.

```toml
[logging]
retention = 30
```
