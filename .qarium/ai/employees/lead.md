# Lead

## Config

| Key            | Value  | Description                                  |
|----------------|--------|----------------------------------------------|
| default_branch | master | Default branch for CI triggers and diff base |

## Architecture & Decisions
- **Plugin framework for pytest with decorator DSL** — `@plugin()` class decorator + `option()` factory define plugins with config, actions, CLI options, env vars, and dependency checking
- **Descriptor-based multi-source option resolution** — PluginOption uses `__get__`/`__set_name__` with priority: plugin_config_key > env_var > command_line > default_from
- **Metaclass wraps pytest_addoption with called_once** — BasePluginMeta prevents duplicate CLI option registration
- **Action pattern with lazy evaluation** — supports both immediate and lazy action execution via deepcopy of ActionContext

## Project Structure
- **define.py — public API decorators** — `@plugin()` and `option()` are the main user-facing entry points
- **pytest.py — pytest integration layer** — BasePlugin, PluginMeta, CommandLine, PluginOption, install_pytest_plugins
- **actions.py — action execution engine** — Action, ActionContext, ActionManager with configure/execute lifecycle
- **utils.py — introspection utility** — `call_context()` accesses caller's globals via `inspect.stack()` for transparent pytest hook injection

## Code Patterns
- **PyHamcrest for test assertions** — `h.assert_that` with matchers, not plain assert or pytest.raises
- **Pytest internal APIs** — imports from `_pytest.main`, `_pytest.config` for tight pytest integration (not the public API)
- **typing.Optional for nullable types** — `t.Optional[X]` everywhere, not `X | None` (Python 3.10 compat)
- **Relative package imports** — `from .module import Class` consistently across the package

## TODO
<!-- empty -->

## LLM Directives
<!-- empty -->

## Lessons

| Problem | Why | How to prevent |
|---------|-----|----------------|