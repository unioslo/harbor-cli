# Scripting

By utilizing the JSON output mode, Harbor CLI can act as a complete replacement for manual API calls using curl in scripts.


A script that looks like this:

```bash
status=$(curl -u "admin:password" -H "Content-Type: application/json" -ki https://demo.goharbor.io/api/v2.0/health | jq ."status")

if [ "$status" == "\"healthy\"" ]; then
    # ...
```

Can be replaced with this:

```bash
status=$(harbor --format json system health | jq ."status")

if [ "$status" == "\"healthy\"" ]; then
    # ...
```

!!! note
    It's recommended to set the [output format](../../configuration/config-file/#outputformat) in the configuration file to `"json"` in order to avoid having to specify `--format json` for every command when using the CLI in scripts.


## Deleting resources

It is recommended to disable the deletion confirmation prompt by using the `--force` option:

```
harbor project delete test-project --force
```

Or by setting the `general.confirm_deletion` option to `false` in the configuration file:

```toml
[general]
confirm_deletion = false
```

## Listing resources

When listing certain resources without any constraints (`--limit` and/or `--query`) there is normally a confirmation prompt to confirm that you want to enumerate all resources. This should be disabled in scripts with the `--no-confirm-enumeration` option:

```
harbor auditlog list --no-confirm-enumeration
```

Or by setting the `general.confirm_enumeration` option to `false` in the configuration file:

```toml
[general]
confirm_enumeration = false
```


<!-- TODO: mention --raw and --no-validate here -->
