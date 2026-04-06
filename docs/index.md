# pluginator

Plugin management system for building pytest plugins with declarative configuration.

## Features

- **Declarative plugin definition** — define plugins with the `@plugin()` decorator
- **Flexible options** — configure plugin options from YAML, environment variables, CLI, or defaults via `option()`
- **Action system** — organize plugin logic into composable actions with `Action` and `ActionContext`
- **Pytest integration** — seamless installation into pytest via `install_pytest_plugins()`
- **Dependency management** — declare plugin dependencies and validate them at runtime

## Quick links

- [Getting Started](getting-started.md) — installation and first plugin
- [API Reference](api-reference.md) — all public classes and functions
- [Configuration](configuration.md) — plugin options and YAML config
- [Examples](examples.md) — usage patterns and workflows
