# API Reference

## Quick Reference

| Entity | Module | Description |
|--------|--------|-------------|
| `plugin()` | `pluginator.define` | Decorator for creating a plugin class |
| `option()` | `pluginator.define` | Create a plugin option descriptor |
| `Action` | `pluginator.actions` | Runnable action bound to a module |
| `ActionContext` | `pluginator.actions` | Context object passed to actions |
| `ActionManager` | `pluginator.actions` | Registry of named actions |
| `CommandLine` | `pluginator.pytest` | Define a pytest CLI option |
| `PluginOption` | `pluginator.pytest` | Descriptor for plugin option resolution |
| `PluginMeta` | `pluginator.pytest` | Plugin metadata dataclass |
| `BasePluginMeta` | `pluginator.pytest` | Metaclass of `BasePlugin` |
| `BasePlugin` | `pluginator.pytest` | Base class for all plugins |
| `install_pytest_plugins()` | `pluginator.pytest` | Install plugins into pytest |
| `call_context()` | `pluginator.utils` | Get caller's global context |

---

## pluginator.define

### `plugin(name, /, *, config=None, default_config=None, deps=None, actions=None)`

Decorator that creates a plugin class with the given metadata.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Plugin name (used for pytest registration) |
| `config` | `str \| None` | `None` | Path to YAML config file |
| `default_config` | `dict \| None` | `None` | Default configuration values |
| `deps` | `list[str] \| None` | `None` | List of dependency plugin names |
| `actions` | `list[Action] \| None` | `None` | List of actions for this plugin |

Returns a decorator that wraps the class, adding `__meta__` and inheriting from `BasePlugin` if not already a subclass.

### `option(opt_type, /, *, strict=True, nullable=False, required=False, env_var=None, default_from=None, plugin_config_key=None, command_line=None, hook=None)`

Create a `PluginOption` descriptor. See [Configuration](configuration.md) for detailed option resolution.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `opt_type` | `type` | required | Option type (e.g. `str`, `int`, `bool`) |
| `strict` | `bool` | `True` | Cast value to `opt_type` when `True` |
| `nullable` | `bool` | `False` | Allow `None` as value |
| `required` | `bool` | `False` | Raise `ValueError` if no value found |
| `env_var` | `str \| None` | `None` | Environment variable name |
| `default_from` | `str \| None` | `None` | Plugin property name for default value |
| `plugin_config_key` | `str \| None` | `None` | Key in YAML config file |
| `command_line` | `CommandLine \| None` | `None` | CLI option definition |
| `hook` | `Callable \| None` | `None` | Transform function applied to value |

---

## pluginator.actions

### `Action(name, module, *, enable=True, default_config=None)`

Represents a runnable action bound to a Python module.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Action name (unique within plugin) |
| `module` | `str` | required | Dotted module path (must define `main()`) |
| `enable` | `bool` | `True` | Whether the action is active |
| `default_config` | `dict \| None` | `None` | Default config passed to `main()` |

The target module must define a `main(config, context)` function. Optionally, it can define a `setup(config)` function called during initialization.

**Properties:** `name`, `enabled`, `setup`, `config`

**Methods:** `configure(action_config)` — resolve the module, `enable` flag, and config from the plugin's YAML `actions` section (see [Configuration](configuration.md))

### `ActionContext`

Base context class passed to actions. Provides:

- `update(**kwargs)` — set attributes; raises `AttributeError` if attribute does not exist
- `validate()` — override for custom validation (no-op by default)

Subclass it to hold action data — `update()` only accepts predefined attributes.

### `ActionManager`

Registry of named actions. Used internally by `BasePlugin`.

Methods:

- `add_action(action, plugin_config)` — register and configure an action; runs its `setup` if enabled
- `__call__(name, context)` — execute an action by name; raises `RuntimeError` if not found

---

## pluginator.pytest

### `CommandLine(opt, /, *args, **kwargs)`

Define a pytest command-line option. Arguments are forwarded to `parser.addoption()`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `opt` | `str` | Option name (e.g. `"--my-flag"`) |
| `*args` | — | Positional args for `addoption` |
| `**kwargs` | — | Keyword args for `addoption` (e.g. `default`, `help`) |

Methods:

- `register_once(opt_type, parser, *, group=None)` — register option with deduplication

### `PluginOption`

Descriptor that resolves a value from multiple sources. See [Configuration](configuration.md) for the resolution chain.

**Properties:** `type`, `command_line`

Methods:

- `init_command_line(parser, *, group=None)` — register CLI option in pytest parser

### `PluginMeta`

Dataclass holding plugin metadata.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Plugin name |
| `actions` | `list[Action]` | `None` | Plugin actions |
| `config_file` | `str \| None` | `None` | YAML config file path |
| `default_config` | `dict \| None` | `None` | Default configuration |
| `dependencies` | `Iterable[str] \| None` | `None` | Required plugin names |

### `BasePluginMeta`

Metaclass of `BasePlugin`. Wraps `pytest_addoption` with `called_once` so repeated installs do not register options twice.

### `BasePlugin`

Base class for all plugins. Created automatically by the `@plugin()` decorator.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `meta` | `PluginMeta` | Plugin metadata |
| `pytest_config` | `Config` | Pytest config (set during initialization) |
| `plugin_config` | `dict` | Merged config from YAML + defaults |
| `plugin_options` | `Iterable[PluginOption]` | All option descriptors |

Methods:

- `action(name, context, *, lazy=False)` — execute or get a lazy wrapper for an action
- `init_plugin_options(parser)` — register all options in pytest parser
- `init_pytest_config(config)` — set pytest config
- `install()` — register plugin in pytest

### `install_pytest_plugins(*plugins, check_deps=True, context=None)`

Install one or more plugins into pytest. Must be called in `conftest.py`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `*plugins` | `BasePlugin` | required | Plugin instances to install |
| `check_deps` | `bool` | `True` | Validate dependencies at collection time |
| `context` | `dict \| None` | `None` | Explicit context (defaults to caller's globals) |

This function injects `pytest_addoption`, `pytest_configure`, and `pytest_collection_finish` hooks into the calling module's context.

---

## pluginator.utils

### `call_context()`

Returns the global context (`f_globals`) of the caller's caller. Used internally by `install_pytest_plugins` to inject pytest hooks into the calling module.
