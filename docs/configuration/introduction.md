# Create a config

## Configuration wizard

Harbor CLI is configured via a TOML configuration file which can be created prior to running for the first time by running the [`init`](../../commands/init/#init_1) command:

```
harbor init
```

This will create a config file at `~/.config/harbor-cli/config.toml`[^1], and then run the interactive configuration wizard. Use the `--no-wizard` flag to skip the configuration wizard.

You can always find the location of the current configuration file by running the [`cli-config path`](../../commands/cli-config/#cli-config-path) command:

```bash
harbor cli-config path
```

!!! info
    `cli-config path` will show the default config file location if no config file is found.


### Alternative config location

To create a configuration file at a location different than the default one, use the `--path` option:

```
harbor init --path /path/to/config.toml
```

The custom file path can then be used when running the application with the `--config` option:

```
harbor --config /path/to/config.toml <command>
```


## Sample config
To print a sample configuration file, use the [`sample-config`](../../commands/sample-config/) command:

```
harbor sample-config > /path/to/config.toml
```

You can combine [`sample-config`](../../commands/sample-config/) with [`cli-config path`](../../commands/cli-config/#cli-config-path) to create a config file at the default location with the sample configuration. This is a non-interactive alternative to using the [`init`](../../commands/init/#init_1) command:

```
harbor sample-config > $(harbor cli-config path)
```

Edit the file to suit your needs:

```
code $(harbor cli-config path)
```

In general, it's better to use [`init`](../../commands/init/#init_1) to create and (re-)configure a configuration file, as it will ensure that the file is valid and that all required fields are present.

[^1]: This project uses [platformdirs](https://pypi.org/project/platformdirs/). See the `user_config_dir` example in the official platformdirs [examples](https://pypi.org/project/platformdirs/#example-output) for up-to-date information on what this resolves to. At the time of writing, this is `~/.config/harbor-cli/config.toml` on Linux, `~/Library/Preferences/harbor-cli/config.toml` on macOS, and `%LOCALAPPDATA%\harbor-cli\config.toml` on Windows.
