# Authentication

Harbor CLI supports multiple authentication methods. The application will try to authenticate using the first method that is available. These methods are:

- [Username and password](#username-and-password)
- [Robot Credentials File](#robot-credentials-file)
- [Basicauth (deprecated)](#basicauth-deprecated)

## Username and password

User password is looked up in the following order:

<!-- NOTE: we could add the envvar and option names by looking up docs/data/options.yaml -->

1. [`--secret` option](#-secret-option)
2. [Environment variable](../../usage/options/#-secret-s)
2. Keyring
3. [Configuration file](../config-file/#harborsecret)


If the user password is not found in any of these locations and no other authentication methods have been provided, the application will prompt for username and password when executing commands that require authentication.

### `--secret` option

A password can be passed in using the [`--secret` option](../../usage/options/#-secret-s):

```
harbor --secret <password> <command>
```


### Environment variable

The password can also be provided by setting the environment variable `HARBOR_CLI_SECRET`:

```
HARBOR_CLI_SECRET=<secret> harbor <command>
```

### Keyring

Harbor CLI has ability to store credentials in your system's keyring via the [keyring](https://pypi.org/project/keyring/) library.

Running [`harbor init`](../../commands/init/) will prompt you for your credentials and store the password in your system's keyring if it is available. The username is always stored in the configuration file.



<!-- TODO: generate this example automatically to keep it up to date? -->

```console
% harbor init

─────────────────────────── ✨ Harbor CLI Configuration Wizard 🧙 ───────────────────────────
? Configure harbor settings? [y/n] (n): y

🚢 Harbor Settings
? Harbor API URL (e.g. https://harbor.example.com/api/v2.0): https://demo.goharbor.io/api/v2.0
? Authentication method ([u]sername/password, [b]asic auth, [f]ile, [s]kip) (s): u
? Harbor username: test-user
? Harbor secret:
! Added password to keyring.
```

Multiple passwords can be stored in the keyring. Changing the username in the configuration file will cause the application to retrieve the password for the given username from the keyring, or prompt for a new one if it's not found.

!!! note

    In order to store the credentials in your system's keyring, extra configuration might be required. See the [installation instructions](../index.md) for your platform to configure keyring.

### Configuration file

If the keyring cannot be used, the credentials will be stored in the configuration file. Similar to the keyring setup, running [`harbor init`](../../commands/init/) will prompt you for your credentials and store them in the configuration file.

```console
% harbor init

────────────────────────────────────────────────── ✨ Harbor CLI Configuration Wizard 🧙 ───────────────────────────────────────────────────
? Configure harbor settings? [y/n] (n): y

🚢 Harbor Settings
? Harbor API URL (e.g. https://harbor.example.com/api/v2.0): https://demo.goharbor.io/api/v2.0
? Authentication method ([u]sername/password, [b]asic auth, [f]ile, [s]kip) (u): u
? Harbor username: test-user
? Harbor secret:
```

## Robot credentials file

Instead of using a personal Harbor account, a Robot account can be used instead. Robot accounts come in two flavors: [Project Robot Accounts](https://goharbor.io/docs/2.5.0/working-with-projects/project-configuration/create-robot-accounts/) and [System Robot Accounts](https://goharbor.io/docs/2.2.0/administration/robot-accounts/). After creating your robot account, you will be prompted to download a JSON file containing the credentials for the account. This file can be specified when launching Harbor CLI by using the  `--credentials-file` option:

```
harbor --credentials-file /path/to/robot/credentials.json <command>
```

Or by setting the environment variable `HARBOR_CLI_CREDENTIALS_FILE`:

```
HARBOR_CLI_CREDENTIALS_FILE=/path/to/robot/credentials.json harbor <command>
```

Or configured in the configuration file:

```toml
[harbor]
credentials_file = "/path/to/robot/credentials.json"
```

!!! warning
    Ensure that the `username` and `secret` config keys and `HARBOR_CLI_USERNAME` and `HARBOR_CLI_SECRET` environment variables are empty or unset, otherwise the application will try to use username/password authentication instead of the credentials file.

## Basicauth (deprecated)

The application also supports supplying credentials as a BASE64-encoded string of `username:secret` using the `--basicauth` option:

```
harbor --basicauth <basicauth> <command>
```

Or by setting the environment variable `HARBOR_CLI_BASICAUTH`:

```
HARBOR_CLI_BASICAUTH=<basicauth> harbor <command>
```

Or by setting the `harbor.basicauth` config key in the configuration file:

```toml
[harbor]
basicauth = "ZG9udDp1c2V0aGlz"
```

!!! warning
    This method is deprecated and will be removed in a future release. It does not improve security in any way over username/password authentication, and is only provided as an implementation detail for the Harbor API.
