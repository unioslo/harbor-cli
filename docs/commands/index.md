# Commands

There are currently {{ commandlist | length }} available commands.

Check the sidebar for more information about each command.

```
{% for command in commandlist -%}
{{ command }}
{% endfor %}
```
