# Formats

## Table: `table`


By default, Harbor-CLI renders results as one or more [Rich](https://rich.readthedocs.io/en/latest/tables.html) tables.
The default tables will always reflect the actual JSON structure of the data, and such
renders each field as a row. Nested values are rendered as separate tables (nesting level is indicated by its color-coded title).

```toml title="config.toml"
[output]
format = "table"
```

``` title="CLI"
harbor --format table system volumes
```

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ SystemInfo                                                                   │
│ ┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field           ┃ Value                                                  ┃ │
│ ┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ storage         │ See below (SystemInfo.storage)                         │ │
│ └─────────────────┴────────────────────────────────────────────────────────┘ │
│ SystemInfo.storage                                                           │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Field                   ┃ Value                                          ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ total                   │ 912470835200                                   │ │
│ │ free                    │ 102376894464                                   │ │
│ └─────────────────────────┴────────────────────────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────╯
```



### Compact tables

The auto-generated tables stay true to the JSON structure of the data, but this can be a bit visually overwhelming. To make the output more readable, you can use the `--table-compact` flag to render the tables in a more compact format. This will only show the most important fields, and will hide nested tables. These tables are more concise, but also more opinionated in their presentation. so they may not be suitable for all use cases.

Not all tables are available to be rendered in this format, and tables that do not have compact representations fall back on the built-in Rich table representation described in the previous section.


<!-- TODO: The following tables have compact representations: -->

```toml
[output.table]
compact=true
```

``` title="CLI"
harbor --format table --table-compact system volumes
```


```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Total Capacity ┃ Free Space ┃ Used Space ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 912.47 GB      │ 102.38 GB  │ 810.09 GB  │
└────────────────┴────────────┴────────────┘
```



## JSON: `json`

Data from API as JSON. This is the raw response from the API. The output is formatted with one value per line and has a default indendation of 2 spaces.

```toml title="config.toml"
[output]
format = "json"

[output.JSON]
indent = 2
```



``` title="CLI"
harbor --format json system volumes
```

```json
{
  "storage": [
    {
      "total": 912470835200,
      "free": 102376873984
    }
  ]
}
```
