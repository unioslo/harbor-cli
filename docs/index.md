# harbor-cli

Harbor CLI is a command line tool for Harbor. It is used to manage Harbor projects, repositories, artifacts, users, and more.

Harbor CLI is powered by [harborapi](https://github.com/pederhan/harborapi) and attempts to follow the Harbor API specification as closely as possible. This means you should be able to expect the same behavior and results from the CLI as you would from the API in the vast majority of cases.

## Installation

Installing the application is generally as simple as running:

```
pipx install git+https://github.com/pederhan/harbor-cli
```

However, on certain platforms this is not sufficient to install all [keyring](https://github.com/jaraco/keyring) dependencies. If you don't care about storing credentials in your system's keyring, you can stop reading here. Otherwise, read on.

### MacOS

```
pipx install git+https://github.com/pederhan/harbor-cli
```

Keyring should work out of the box on MacOS >=11 with Python >=3.8.7.


### Linux

Depending on your Linux flavor and choice of keyring backend, you may need to install additional packages. See the [keyring documentation](https://keyring.readthedocs.io/en/latest/#installing-keyring) for more information.

To inject a package into the application's pipx environment, use the `pipx inject` command:


```
pipx install git+https://github.com/pederhan/harbor-cli
pipx inject harbor-cli <package to inject>
```

Follow the instructions for your Linux flavor and keyring backend to determine which package to inject (if any). If a package requires compilation and you don't have the necessary prerequisites installed, installing the package as a system package through your system's package manager may be easier.

### Windows

```
pipx install git+https://github.com/pederhan/harbor-cli
```

Keyring functionality is untested on Windows, but should work out of the box. If you run into any issues, consult the [keyring documentation](https://github.com/jaraco/keyring#readme) for more information. Otherwise, please open an issue.
