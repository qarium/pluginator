# Examples

## Basic plugin

Create a plugin with a configurable option and install it into pytest.

**conftest.py**

```python
from pluginator.define import plugin, option
from pluginator import install_pytest_plugins

@plugin("greeter", config="greeter.yaml")
class GreeterPlugin:
    greeting = option(str, env_var="GREETING", default_from="default_greeting")

    def default_greeting(self):
        return "Hello"

install_pytest_plugins(GreeterPlugin())
```

**greeter.yaml**

```yaml
greeting: "Hi there"
```

---

## Plugin with actions

Define actions that run when called from your plugin or tests.

**my_plugin/__init__.py**

```python
from pluginator.define import plugin, option
from pluginator import Action

@plugin("reporter", actions=[
    Action("generate", "my_plugin.actions.generate", default_config={"format": "text"}),
])
class ReporterPlugin:
    output_dir = option(str, env_var="REPORT_DIR", default_from="default_dir")

    def default_dir(self):
        return "/tmp/reports"
```

**my_plugin/actions/generate.py**

```python
def setup(config):
    # Called once during plugin initialization
    pass

def main(config, context):
    format = config.get("format", "text")
    output_dir = context.output_dir
    # Generate report...
```

---

## CLI options

Add pytest command-line options that feed into plugin configuration.

**conftest.py**

```python
from pluginator.define import plugin, option
from pluginator import CommandLine, install_pytest_plugins

@plugin("runner")
class RunnerPlugin:
    retries = option(
        int,
        command_line=CommandLine("--retries", default=1, help="Number of retries"),
        env_var="RUNNER_RETRIES",
    )
    verbose = option(
        bool,
        command_line=CommandLine("--runner-verbose", action="store_true", default=False),
    )

install_pytest_plugins(RunnerPlugin())
```

Run with:

```bash
pytest --retries 3 --runner-verbose
```

---

## Plugin dependencies

Declare dependencies that are validated at collection time.

```python
from pluginator.define import plugin
from pluginator import install_pytest_plugins

@plugin("db-fixtures", deps=["postgres"])
class DbFixturesPlugin:
    ...

@plugin("postgres")
class PostgresPlugin:
    ...

# Order matters — install the dependency first
install_pytest_plugins(PostgresPlugin(), DbFixturesPlugin())
```

If `postgres` is not installed when `db-fixtures` runs, pytest raises an `AssertionError`.
