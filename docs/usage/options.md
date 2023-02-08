# Options

## Global options

Global options are options that apply to every command. They are usually overrides of configuration values, such as the Harbor URL, username, password, etc. They must be specified before the command to run, e.g.:

```
harbor \
--harbor-url https://my-harbor.com/api/v2.0 \
--harbor-username admin \
--harbor-secret my-secret \
project list
```

{% for option in options %}
## {{ option['params'] }}

**Environment variable:** `{{ option['envvar'] }}`

{{ option['help'] }}

{%- endfor %}
