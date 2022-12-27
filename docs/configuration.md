# Configuration

Harbor CLI is configured via a TOML configuration file which must be created prior to running for the first time. This configuration file can be created by running the command:

```
harbor init
```

This will create a config file with default values at `~/.config/harbor-cli/config.toml` (depends on your platform). Before you can use Harbor CLI, you will need to edit this file to add your Harbor URL and credentials (username+secret, base64 credentials or JSON credentials file).

In the future, a configuration wizard will be added to make this process easier.

## Sample configuration file

```toml
{% include "sample_config.toml" %}
```

**NOTE**: The name of the `output.JSON` table is case-sensitive. The reason this name is upper-case is due to a conflict with the built-in Pydantic `json` method. This will hopefully be fixed in a future release.

## Custom configuration file location
A custom configuration file can be created with the help of the `sample-config` command:

```
harbor sample-config > /path/to/config.toml
```

The custom file can then be specified when running the application with the `--config` option:

```
harbor --config /path/to/config.toml <command>
```
