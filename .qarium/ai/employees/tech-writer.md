# Tech Writer Config

## Config

| Key           | Value                                    | Description                         |
|---------------|------------------------------------------|-------------------------------------|
| build_cmd     | mkdocs build                             | Build validation command            |
| deploy_cmd    | mkdocs gh-deploy --force                 | Deploy command                      |
| examples_file | docs/examples.md                         | File for usage examples             |
| logo_url      | https://avatars.githubusercontent.com/u/262344922?s=200&v=4 | Standard qarium logo |
| base_branch   | 0.0.x                                    | Base branch for git diff comparison |

## Rules

### Mapping

| Source path | Documentation files |
|-------------|---------------------|
| `pluginator/define.py` | `docs/getting-started.md`, `docs/api-reference.md` |
| `pluginator/actions.py` | `docs/api-reference.md` |
| `pluginator/pytest.py` | `docs/api-reference.md`, `docs/configuration.md`, `docs/examples.md` |
| `pluginator/utils.py` | `docs/api-reference.md` |
| `pyproject.toml` | `docs/getting-started.md`, `docs/index.md` |

### Conventions

- API Reference starts with a Quick Reference summary table, followed by detailed sections per module
- Examples are separated by `---` horizontal rules
- Configuration presents the option resolution priority chain as a table

## Lessons

| Problem | Why | How to prevent |
|---------|-----|----------------|
