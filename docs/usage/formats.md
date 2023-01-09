# Formats

## Table: `table`


The default output format. Renders the result as one or more Rich tables. Example:

```
harbor --format table system info
```

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ GeneralInfo                                                                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field                              ┃ Value                               ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ current_time                       │ 2023-01-09 13:56:00.086000+00:00    │ │
│ │ with_notary                        │ False                               │ │
│ │ with_chartmuseum                   │ False                               │ │
│ │ registry_url                       │ harbor.example.com                  │ │
│ │ external_url                       │ https://harbor.example.com          │ │
│ │ auth_mode                          │ ldap_auth                           │ │
│ │ project_creation_restriction       │ adminonly                           │ │
│ │ self_registration                  │ False                               │ │
│ │ has_ca_root                        │ False                               │ │
│ │ harbor_version                     │ v2.5.4-a39bd2bc                     │ │
│ │ registry_storage_provider_name     │ filesystem                          │ │
│ │ read_only                          │ False                               │ │
│ │ notification_enable                │ True                                │ │
│ │ authproxy_settings                 │ None                                │ │
│ └────────────────────────────────────┴─────────────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## JSON: `json`

Data from API as JSON

```
harbor --format json system info
```

```json
{
  "current_time": "2023-01-09T13:59:41.070000+00:00",
  "with_notary": false,
  "with_chartmuseum": false,
  "registry_url": "harbor.example.com",
  "external_url": "https://harbor.example.com",
  "auth_mode": "ldap_auth",
  "project_creation_restriction": "adminonly",
  "self_registration": false,
  "has_ca_root": false,
  "harbor_version": "v2.5.4-a39bd2bc",
  "registry_storage_provider_name": "filesystem",
  "read_only": false,
  "notification_enable": true,
  "authproxy_settings": null
}
```

## JSON with schema: `jsonschema`

Data from API + metadata as JSON


```
harbor --format jsonschema system info
```

```json
{
  "version": "1.0.0",
  "type": "GeneralInfo",
  "module": "harborapi.models.models",
  "data": {
    "current_time": "2023-01-09T14:01:09.938000+00:00",
    "with_notary": false,
    "with_chartmuseum": false,
    "registry_url": "harbor.example.com",
    "external_url": "https://harbor.example.com",
    "auth_mode": "ldap_auth",
    "project_creation_restriction": "adminonly",
    "self_registration": false,
    "has_ca_root": false,
    "harbor_version": "v2.5.4-a39bd2bc",
    "registry_storage_provider_name": "filesystem",
    "read_only": false,
    "notification_enable": true,
    "authproxy_settings": null
  }
}
```

The intention with this format is to be able to load the data into a Python object of the correct type. This is useful for being able to load any `harborapi`[https://github.com/pederhan/harborapi] object and display it as a table, or to use any special methods that the object may have. See [harbor_cli.output.schema][] for more information.

This feature is under development, and there is currently no functionality in place for utilizing this. The functionality for loading from a schema file is defined by [harbor_cli.output.schema.Schema.from_file][].
