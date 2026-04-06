# pluginator

Plugin management system

## Installation

```bash
pip install pluginator
```

## Quick Start

```python
from pluginator import define

@define.plugin('my-plugin', config='config.yml')
class MyPlugin:
    name = define.option(str, required=True, env_var='PLUGIN_NAME')

    def configure(self):
        print(f'Configured: {self.name}')
```

## Documentation

Full documentation: https://qarium.github.io/pluginator/