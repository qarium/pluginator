# DevOps

## Config

| Key            | Value            | Description                                 |
|----------------|------------------|---------------------------------------------|
| ci_provider    | github-actions   | CI provider                                 |
| trigger_branch | 0.0.x            | Default branch for triggers                 |
| diff_range     | HEAD~5           | Git diff range for auto-analysis in feature |

## Rules

### Workflow Registry

| Workflow    | File              | Trigger                                       | Purpose                                      |
|-------------|-------------------|-----------------------------------------------|----------------------------------------------|
| Lint        | lint.yml          | push/PR to 0.0.x                              | Ruff lint + format check                     |
| Tests       | tests.yml         | push/PR to 0.0.x                              | Pytest across Python 3.10–3.14               |
| Docs        | docs.yml          | push to 0.0.x                                 | MkDocs build + deploy to GitHub Pages        |
| Publish     | publish.yml       | workflow_dispatch from X.Y.x branch           | Build, publish to PyPI, create GitHub Release|
| New Version | new_version.yml   | workflow_dispatch from default branch         | Create X.Y.x branch, set as default          |
| Notify      | notify.yml        | workflow_run after Publish Release success     | Telegram notification on release             |
| Strictacode | strictacode.yml   | push/PR to 0.0.x                              | Code quality analysis                        |

### Conventions

- `tests.yml`, `publish.yml`, `new_version.yml`, `notify.yml` — caller-паттерн (`uses: qarium/ci`), не содержат steps
- `lint.yml`, `docs.yml`, `strictacode.yml` — project-specific, полная реализация

## Lessons

| Problem | Why | How to prevent |
|---------|-----|----------------|