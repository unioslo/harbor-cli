# Global Options

Global options are options that apply to every command, and are usually overrides for configuration file options. For persistent configuration of these options, see [Configuration](../configuration/config-file).

Global options must be specified before the command to run, e.g.:

```
harbor \
--url https://my-harbor.com/api/v2.0 \
--username admin \
--secret my-secret \
project list
```

{% for option in options %}

----

## {{ option['params'] }}
{% if option['envvar'] %}
**Environment variable:** `{{ option['envvar'] }}`
{%- endif %}
{% if option['config_value'] %}
**Configuration option:** [`{{ option['config_value'] }}`](../configuration/config-file.md#{{option['fragment']}})
{%- endif %}

{{ option['help'] }}
{%- endfor %}
