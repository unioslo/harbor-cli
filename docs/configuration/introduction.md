# Creating a config

Harbor CLI is configured via a TOML configuration file which must be created prior to running for the first time. This configuration file can be created by running the command:

```
harbor init
```

This will create a config file at `~/.config/harbor-cli/config.toml`[^1], and then run the interactive configuration wizard. Use the `--no-wizard` flag to skip the configuration wizard.

!!! important
    The configuration file is required to run the application. Running without a configuration file will call `harbor init` and create a configuration file at the default location.

To create a configuration file at a location different than the default one, use the `--path` option:

```
harbor init --path /path/to/config.toml
```

The custom file path can then be specified when running the application with the `--config` option:

```
harbor --config /path/to/config.toml <command>
```


## Print sample configuration file to stdout
To print a sample configuration file, use the `sample-config` command:

```
harbor sample-config
```

This can then be combined with the `>` operator to redirect the output to a file:

```
harbor sample-config > /path/to/config.toml
```

[^1]: This project uses [platformdirs](https://pypi.org/project/platformdirs/). See the `user_config_dir` example in the official platformdirs [examples](https://pypi.org/project/platformdirs/#example-output) for up-to-date information on what this resolves to. At the time of writing, this is `~/.config/harbor-cli/config.toml` on Linux, `~/Library/Preferences/harbor-cli/config.toml` on macOS, and `%LOCALAPPDATA%\harbor-cli\config.toml` on Windows.
