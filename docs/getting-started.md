# Getting Started

## Installation

```bash
pip install pluginator
```

Requires Python 3.10 or newer.

## Quick Start

### 1. Define a plugin

Use the `@plugin()` decorator to create a plugin class:

```python
from pluginator.define import plugin, option
from pluginator import Action

@plugin("my-plugin", config="my_plugin.yaml", actions=[
    Action("greet", "my_plugin.actions.greet"),
])
class MyPlugin:
    message = option(
        str,
        plugin_config_key="message",
        env_var="MY_PLUGIN_MESSAGE",
        default_from="default_message",
    )
    count = option(int, plugin_config_key="count", default_from="default_count")

    def default_message(self):
        return "Hello"

    def default_count(self):
        return 1
```

### 2. Create an action module

Each action references a module with a `main` function:

```python
# my_plugin/actions/greet.py
def main(config, context):
    print(f"{config['message']} " * config['count'])
```

### 3. Install into pytest

In your `conftest.py`, call `install_pytest_plugins`:

```python
from pluginator import install_pytest_plugins
from my_plugin import MyPlugin

install_pytest_plugins(MyPlugin())
```

### 4. Configure (optional)

Create a YAML config file (`my_plugin.yaml`):

```yaml
message: "Hello from config"
count: 3
```

Plugin options are resolved in priority order: **YAML config key → environment variable → CLI argument → default property → type default**. An option reads the YAML file only when `plugin_config_key` is set — that is why the options above pass `plugin_config_key`.
