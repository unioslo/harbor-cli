# Options

The application provides a wide range of options that can be used to customize its behavior. Common for all these options is that they must be specified before the command to run:

```
harbor \
--url https://my-harbor.com/api/v2.0 \
--username admin \
--secret my-secret \
project list
```

Many of these options can override configuration file options, and will always take precedence if used. For a more in-depth look at persistent configuration, see [Configuration](../../configuration/config-file). Each option listed below has a link to the relevant section in the configuration file if applicable.


{% for option in options %}

----

## {{ option['params'] }}
{% if option['envvar'] %}
**Environment variable:** `{{ '`' + (option['envvar'] | join('`, `')) + '`' }}`
{%- endif %}
{% if option['config_value'] %}
**Configuration option:** [`{{ option['config_value'] }}`](../configuration/config-file.md#{{option['fragment']}})
{%- endif %}

{{ option['help'] }}
{%- endfor %}
