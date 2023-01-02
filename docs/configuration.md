# Configuration

Harbor CLI is configured via a TOML configuration file which must be created prior to running for the first time. This configuration file can be created by running the command:

```
harbor init
```

This will create a config file at `~/.config/harbor-cli/config.toml` (depends on your platform), and then run the interactive configuration wizard. Specify the `--no-wizard` flag to skip the configuration wizard.

!!! important
    The configuration file is required to run the application. Running without a configuration file will call `harbor init` and create a configuration file at the default location.

To create a configuration file at a specific location, use the `--path` option:

```
harbor init --path /path/to/config.toml
```

## Sample configuration file

```toml
{% include "sample_config.toml" %}
```

**NOTE**: The name of the `output.JSON` table is case-sensitive. The reason this name is upper-case is due to a conflict with the built-in Pydantic `json` method. This will hopefully be fixed in a future release.

## Print sample configuration file to stdout
To print a sample configuration file, use the `sample-config` command:

```
harbor sample-config
```

This can then be combined with the `>` operator to redirect the output to a file:

```
harbor sample-config > /path/to/config.toml
```

The custom file can then be specified when running the application with the `--config` option:

```
harbor --config /path/to/config.toml <command>
```
