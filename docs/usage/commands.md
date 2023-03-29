# Commands

There are currently {{ commandlist | length }} available commands.

For more information about a specific command, use:

```
harbor <command> --help
```

See [Commands](../commands/index.md) for usage info of each command.


## Search for commands

To search for a command based on name or description, use:

```
harbor find QUERY... [OPTIONS]
```

See [`harbor find`](../commands/find.md) for more information.


## List of commands

```
{% for command in commandlist -%}
{{ command }}
{% endfor %}
```
