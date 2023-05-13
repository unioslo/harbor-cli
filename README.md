# harbor-cli

<!-- [![PyPI - Version](https://img.shields.io/pypi/v/harbor-cli.svg)](https://pypi.org/project/harbor-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/harbor-cli.svg)](https://pypi.org/project/harbor-cli) -->

-----

**NOTE**: This project is still in early development, and most functionality, such as CLI options and configuration file format, is subject to change. Prior to version 1.0.0, breaking changes may be introduced in minor version updates.

**Table of Contents**

- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [Examples](#examples)
- [License](#license)

## Installation

<!-- ```console
pip install harbor-cli
``` -->

The name `harbor-cli` is in the process of being acquired from its current owner on PyPI.

In the meantime, you can install the package from GitHub, preferably with `pipx`:

```
pipx install git+https://github.com/pederhan/harbor-cli
```

Before the name acquisition process is complete, semantic versioning will not be adhered to and breaking changes may be introduced at any point. Once the package is available on PyPI, semantic versioning will be adhered to and breaking changes will only be introduced in major version updates.

## Features

- 150+ commands
- Beautiful command-line interface powered by [Typer](https://github.com/tiangolo/typer) and [Rich](https://github.com/Textualize/rich).
- REPL mode (`harbor repl`)
- Tab completion for commands and options.
- Automatic retrying of failed requests
- Multiple output formats:
    - Table
    - JSON
- Large number of configuration options
    - Authentication methods
    - Table styling
    - Output formats
    - ... and more


## Usage

```
harbor --help
```

Check the [documentation](https://pederhan.github.io/harbor-cli/) for more information.


## Examples

Most commands produce some sort of table. While the most common methods have nice hand-written tables, some of the tables are generated automatically from the data returned by the API.

PRs are always welcome if you wish to add a new table or improve an existing one.

This first example in this section is an automatically generated table, while the subsequent examples all feature hand-made tables.


### Create project

```console
$ harbor project create test-project2 --public true
[INFO] Created project 'test-project2'
╭──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ProjectCreateResult                                                                              │
│ ┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field             ┃ Value                                                                    ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ location          │ /api/v2.0/projects/test-project2                                         │ │
│ │ project           │ See below (ProjectCreateResult.project)                                  │ │
│ └───────────────────┴──────────────────────────────────────────────────────────────────────────┘ │
│ ProjectCreateResult.project                                                                      │
│ ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field                ┃ Value                                                                 ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ project_name         │ test-project2                                                         │ │
│ │ public               │ None                                                                  │ │
│ │ metadata             │ See below (ProjectCreateResult.project.metadata)                      │ │
│ │ cve_allowlist        │ None                                                                  │ │
│ │ storage_limit        │ None                                                                  │ │
│ │ registry_id          │ None                                                                  │ │
│ └──────────────────────┴───────────────────────────────────────────────────────────────────────┘ │
│ ProjectCreateResult.project.metadata                                                             │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field                                                                     ┃ Value            ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩ │
│ │ public                                                                    │ true             │ │
│ │ enable_content_trust                                                      │ None             │ │
│ │ enable_content_trust_cosign                                               │ None             │ │
│ │ prevent_vul                                                               │ None             │ │
│ │ severity                                                                  │ None             │ │
│ │ auto_scan                                                                 │ None             │ │
│ │ reuse_sys_cve_allowlist                                                   │ None             │ │
│ │ retention_id                                                              │ None             │ │
│ └───────────────────────────────────────────────────────────────────────────┴──────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Update project

```console
harbor project update test-project --public false --severity high --auto-scan true
[INFO] Updated project 'test-project'
```

### Get project


```console
$ harbor project get test-project
╭────────────────────────────────────────── test-project ──────────────────────────────────────────╮
│                                             Project                                              │
│ ┏━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ ID  ┃ Name           ┃ Public  ┃ Owner     ┃ Repositories   ┃ Charts  ┃ Created              ┃ │
│ ┡━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ 6   │ test-project   │ false   │ pederhan  │ 0              │ None    │ 2023-05-13 10:29:56  │ │
│ └─────┴────────────────┴─────────┴───────────┴────────────────┴─────────┴──────────────────────┘ │
│                                         Project Metadata                                         │
│ ┏━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┓ │
│ ┃        ┃           ┃ Content   ┃            ┃           ┃           ┃            ┃           ┃ │
│ ┃        ┃ Content   ┃ Trust     ┃ Vuln       ┃ Max       ┃           ┃ Reuse Sys  ┃ Retention ┃ │
│ ┃ Public ┃ Trust     ┃ Cosign    ┃ Prevention ┃ Severity  ┃ Auto Scan ┃ CVE List   ┃ ID        ┃ │
│ ┡━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━┩ │
│ │ False  │ False     │ False     │ False      │ high      │ True      │ False      │ None      │ │
│ └────────┴───────────┴───────────┴────────────┴───────────┴───────────┴────────────┴───────────┘ │
│                                          CVE Allowlist                                           │
│ ┏━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ ID   ┃ Items     ┃ Expires     ┃ Created                      ┃ Updated                      ┃ │
│ ┡━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ 6    │ None      │ None        │ 0001-01-01 00:00:00          │ 0001-01-01 00:00:00          │ │
│ └──────┴───────────┴─────────────┴──────────────────────────────┴──────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Get project (JSON format)

```
$ harbor --format json project get test-project
```
```json
{
  "chart_count": null,
  "creation_time": "2023-05-13T10:29:56.214000+00:00",
  "current_user_role_id": 1,
  "current_user_role_ids": [
    1
  ],
  "cve_allowlist": {
    "creation_time": "0001-01-01T00:00:00+00:00",
    "expires_at": null,
    "id": 6,
    "items": [],
    "project_id": 6,
    "update_time": "0001-01-01T00:00:00+00:00"
  },
  "deleted": null,
  "metadata": {
    "auto_scan": "true",
    "enable_content_trust": null,
    "enable_content_trust_cosign": null,
    "prevent_vul": null,
    "public": "false",
    "retention_id": null,
    "reuse_sys_cve_allowlist": null,
    "severity": "high"
  },
  "name": "test-project",
  "owner_id": 7,
  "owner_name": "pederhan",
  "project_id": 6,
  "registry_id": null,
  "repo_count": 0,
  "togglable": null,
  "update_time": "2023-05-13T10:29:56.214000+00:00"
}
```



### System info


<!-- All examples are running with COLUMNS=100. -->

```console
$ harbor system info
╭────────────────────────────────────────── System Info ───────────────────────────────────────────╮
│                                             General                                              │
│ ┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓ │
│ ┃                ┃                ┃               ┃ Registry       ┃           ┃               ┃ │
│ ┃                ┃                ┃ Harbor        ┃ Storage        ┃           ┃               ┃ │
│ ┃ Registry URL   ┃ External URL   ┃ Version       ┃ Provider       ┃ Read Only ┃ Nested Notary ┃ │
│ ┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩ │
│ │ demo.goharbor. │ https://demo.g │ v2.8.0-89ef15 │ filesystem     │ False     │ True          │ │
│ │ io             │ oharbor.io     │ 6d            │                │           │               │ │
│ └────────────────┴────────────────┴───────────────┴────────────────┴───────────┴───────────────┘ │
│                                          Authentication                                          │
│ ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓ │
│ ┃ Mode    ┃ Primary Auth Mode ┃ Project Creation Restriction ┃ Self Registration ┃ Has CA Root ┃ │
│ ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩ │
│ │ db_auth │ False             │ everyone                     │ True              │ False       │ │
│ └─────────┴───────────────────┴──────────────────────────────┴───────────────────┴─────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### System health

```console
$ harbor system health
╭───────────────────────────────────────── System Health ──────────────────────────────────────────╮
│ Status: healthy                                                                                  │
│                                            Components                                            │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Component                                ┃ Status                      ┃ Error               ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ core                                     │ healthy                     │ None                │ │
│ │ database                                 │ healthy                     │ None                │ │
│ │ jobservice                               │ healthy                     │ None                │ │
│ │ notary                                   │ healthy                     │ None                │ │
│ │ portal                                   │ healthy                     │ None                │ │
│ │ redis                                    │ healthy                     │ None                │ │
│ │ registry                                 │ healthy                     │ None                │ │
│ │ registryctl                              │ healthy                     │ None                │ │
│ │ trivy                                    │ healthy                     │ None                │ │
│ └──────────────────────────────────────────┴─────────────────────────────┴─────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## License

`harbor-cli` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
