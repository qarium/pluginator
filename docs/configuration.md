# Configuration

## YAML config file

Plugins can read configuration from a YAML file. Set the path in the `@plugin()` decorator:

```python
@plugin("my-plugin", config="my_plugin.yaml")
class MyPlugin:
    ...
```

The YAML file is loaded with `yaml.full_load` and merged with `default_config`:

```python
@plugin("my-plugin", config="my_plugin.yaml", default_config={"timeout": 30})
class MyPlugin:
    ...
```

```yaml
# my_plugin.yaml
timeout: 60
verbose: true
```

Result: `{"timeout": 60, "verbose": True}` — YAML values override defaults.

## Plugin options

Options are created with `option()` and defined as class-level descriptors:

```python
@plugin("my-plugin", config="my_plugin.yaml")
class MyPlugin:
    message = option(str, env_var="MY_MESSAGE")
    count = option(int, default_from="default_count")
    debug = option(bool, command_line=CommandLine("--my-debug", action="store_true", default=False))

    def default_count(self):
        return 5
```

### Resolution chain

When a plugin option is accessed, values are resolved in this priority order:

| Priority | Source | Parameter | Example |
|----------|--------|-----------|---------|
| 1 | YAML config | `plugin_config_key` | `my_plugin.yaml` → key |
| 2 | Environment variable | `env_var` | `MY_MESSAGE=hello` |
| 3 | CLI argument | `command_line` | `--my-debug` |
| 4 | Default property | `default_from` | `default_count` method |
| 5 | Required check | `required=True` | Raises `ValueError` if no value |
| 6 | Type default / None | `nullable` | `None` if `nullable=True`, else `type()` |

The first non-`None` source wins. If `hook` is set, it transforms the value before type casting.

### Option parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `opt_type` | `type` | required | Value type for casting |
| `strict` | `bool` | `True` | Apply `opt_type()` cast when `True` |
| `nullable` | `bool` | `False` | Return `None` instead of type default |
| `required` | `bool` | `False` | Raise if no value resolved |
| `env_var` | `str` | `None` | Environment variable name |
| `default_from` | `str` | `None` | Plugin method/property name |
| `plugin_config_key` | `str` | `None` | YAML config key |
| `command_line` | `CommandLine` | `None` | pytest CLI option |
| `hook` | `Callable` | `None` | Value transform function |

## Actions configuration

Actions can be configured via the plugin's YAML file under the `actions` key:

```yaml
# my_plugin.yaml
actions:
  greet:
    enable: false
    module: my_plugin.actions.greet
    config:
      message: "Custom message"
```

| Action config key | Type | Description |
|-------------------|------|-------------|
| `enable` | `bool` | Enable or disable the action |
| `module` | `str` | Override the action's module path |
| `config` | `dict` | Override action's default config |
