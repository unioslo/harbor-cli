# Commands

There are currently {{ commandlist | length }} available commands.

For more information about a specific command, use:

```
harbor <command> --help
```


## Search for commands

To search for a command based on name or description, use:

```
harbor find QUERY... [OPTIONS]
```

See `harbor find --help` for more information.


## Command list

```
{% for command in commandlist %}
{{ command }}
{%- endfor %}
```
