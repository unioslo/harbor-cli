# Options

## Global options

Global options are options that apply to every command. They are usually overrides of configuration values, such as the Harbor URL, username, password, etc. They must be specified before the command to run, e.g.:

```
harbor \
--url https://my-harbor.com/api/v2.0 \
--username admin \
--secret my-secret \
project list
```

{% for option in options %}
## {{ option['params'] }}
{% if option['envvar'] %}
**Environment variable:** `{{ option['envvar'] }}`
{%- endif %}
{% if option['config_value'] %}
**Configuration value:** [`{{ option['config_value'] }}`](../configuration/config-file.md#{{option['fragment']}})
{%- endif %}

{{ option['help'] }}

{%- endfor %}
