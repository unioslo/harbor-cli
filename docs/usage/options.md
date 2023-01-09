# Options

## Global options

Global options are options that apply to every command. They are usually overrides of configuration values, such as the Harbor URL, username, password, etc. They must be specified before the command to run, e.g.:

```
harbor \
--harbor-url https://my-harbor.com/api/v2.0 \
--harbor-username admin \
--harbor-secret my-secret \
project list
```

### `--config`

Path to a configuration file to use. If not specified, the default configuration file will be used.

### `--harbor-url`

URL of the Harbor instance to connect to. Overrides the Harbor URL specified in the configuration file.

### `--harbor-username`

Username to use when connecting to the Harbor instance. Overrides the username specified in the configuration file.

### `--harbor-secret`

Secret (password) to use when connecting to the Harbor instance. Overrides the password specified in the configuration file.

### `--harbor-credentials`

Base64-encoded basic access credentials to use when connecting to the Harbor instance. Overrides the credentials specified in the configuration file.

### `--harbor-credentials-file`

The path to a JSON file containing Harbor authentication info to use when connecting to the Harbor instance. Overrides the credentials file specified in the configuration file.

### `--table-description`/`--no-table-description`

Enable/disable table description columns. Overrides the `output.table.description` configuration value.

### `--table-max-depth`

Specifies depth to recurse when rendering nested data structures as tables. A value of `-1` disables recursion. Overrides the `output.table.max_depth` configuration value.

<!-- TODO: fix this when max_depth=0 disables recursion -->

### `--table-compact`/`--table-no-compact`

Enable/disable compact table rendering. Overrides the `output.table.compact` configuration value. Compact tables are custom tables that are rendered in a more compact format, sometimes omitting columns that are not relevant to the current context.

Disabling this option will render tables in the default format defined in [harborapi](https://pederhan.github.io/harborapi/reference/models/base/#harborapi.models.base.BaseModel.as_panel), which is more verbose.

### `--json-indent`

Specifies the number of spaces to indent when rendering JSON output. Overrides the `output.json.indent` configuration value.

### `--json-sort-keys`

Enable/disable sorting of JSON keys. Overrides the `output.json.sort_keys` configuration value.

### `--format`/`-f`

Specifies the output format to use. Overrides the `output.format` configuration value.

The available values are
{%- for format in formats %}
`{{ format }}`{%- if not loop.last %}, {% endif -%}
{%- endfor %}

See [Formats](../formats) for more information.


## `<subcommand> list` options

Most resources can be listed using the `<type of resource> list` command, e.g. `project list`, `repository list`, `scanner list`, etc.

The following options are supported by the various `list` subcommands.

### `--query`

Query string used to query/filter resources.
Only the resources that match the query string will be returned. If a field that is not supported by the resource is specified in the query string, the it will be ignored. This is a Harbor API implementation detail, and might change in the future.

Supported query patterns are:

* Exact match: `k=v`
* Fuzzy match: `k=~v`
* Range: `k=[min~max]`
* List with union releationship: `k={v1 v2 v3}`
* List with intersetion relationship: `k=(v1 v2 v3)`.

The value of range and list can be string, integer or time (in the format  `"2020-04-09 02:36:00"`). Query patterns can be combined by separating them with `","`. e.g.

```
--query "k1=v1,k2=~v2,k3=[min~max]"
```


Values with spaces must be enclosed in quotes. e.g.

```
--query "k1=v1,k2=~v2,k3=[min~max],k4='2020-04-09 02:36:00'"
```

Always enclose the query pattern in quotes to avoid shell expansion. Use different quotes for the enclosing quotes and the quotes around the value.


### `--sort`

Sorting order of the resources. The value of the option is a comma-separated list of fields to sort by. By default, fields are sorted in ascending order. Use `-` to denote that the field should be sorted in descending order.

Sort field1 ascending and field2 descending:

```
--sort "field1,-field2"
```

Enclose the value in quotes to avoid shell expansion.


### `--page`

Page number of page to start fetching resources from. The default value is 1. This should ideally never be changed, but is exposed for completeness.

### `--page-size`

Number of resources to fetch per page. The default value is 10, but can be changed to any positive integer value. Again, not expected to be changed, but is exposed for completeness.
