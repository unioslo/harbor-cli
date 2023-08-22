# Commands

There are currently {{ commandlist | length }} available commands.

Check the sidebar for more information about each command.

!!! important
    A configuration file is required to use most commands. Using these commands without an existing configuration file will run [`init`](./init/#init_1) in wizardless mode and create a configuration file at the default location.

    See [Configuration](../configuration/introduction/#configuration) for more information about the configuration file.


## Available commands

```
{% for command in commandlist -%}
{{ command }}
{% endfor %}
```
