# Formats

## Table: `table`

By default, the application renders result as tables. These tables try to display the most important information in a concise and readable format. The compact tables use plain English and format data such as size (bytes) to the appropriate units to make the information more easily digestible.

<!-- TODO: The following tables have compact representations: -->

```toml title="config.toml"
[output]
format = "table"
```

``` title="CLI"
harbor --format table system volumes
```

```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Total Capacity ┃ Free Space ┃ Used Space ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 912.47 GB      │ 102.38 GB  │ 810.09 GB  │
└────────────────┴────────────┴────────────┘
```

There are over 150 different data structures in the Harbor API specification, and not all of them have been given a custom compact table representation in the application yet. In these cases, the application falls back on more crude auto-generated tables, which are described in the next section.

### Auto-generated tables

Not all models in the API have a custom compact table representation, and the application will fall back on creating auto-generated tables for these. The auto-generated tables always reflect the actual JSON structure of the data, and therefore renders each key-value pair as separate rows. Nested models are rendered as separate tables with a reference to the nested model through its name in the parent table. Nesting level is indicated by a table's color-coded, dot-separated title.

```toml title="config.toml"
[output]
format = "table"

[output.table]
compact = false
```

``` title="CLI"
harbor --format table --no-table-compact system volumes
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

!!! info
    The `SystemInfo` table contains a nested model under the key `storage`. This name is used as the title of the table representing the nested model.

In the future, we aim to have custom compact table representations for all models in the API. However, if you prefer the auto-generated tables, you can always disable the compact tables by setting `ouput.table.compact` to `false` in your configuration file or by passing in `--no-table-compact` to the CLI.



## JSON: `json`

Render the data from the API as JSON. This emulates the presentation of the raw response from the API. The output is formatted with one value per line and has a default indendation of 2 spaces.

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
