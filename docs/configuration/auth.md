# Authentication

By default, the application will try to save user credentials to the system's keyring via the [keyring](https://pypi.org/project/keyring/) library. If the keyring is not available, the credentials will be saved to the configuration file.

User password is looked up in the following order:

<!-- NOTE: we could add the envvar and option names by looking up docs/data/options.yaml -->

1. [Environment variable](../../usage/options/#-secret-s)
2. [`--secret` option](../../usage/options/#-secret-s)
2. Keyring
3. [Configuration file](../config-file/#harborsecret)


If the user password is not found in any of these locations, the application will prompt for it.
