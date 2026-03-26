# DevOps

## Config

| Key            | Value          | Description                                 |
|----------------|----------------|---------------------------------------------|
| ci_provider    | github-actions | CI provider                                 |
| trigger_branch | main           | Default branch for triggers                 |
| diff_range     | HEAD~5         | Git diff range for auto-analysis in feature |

## Rules

### Workflow Registry

| Workflow | File                            | Trigger   | Purpose     |
|----------|---------------------------------|-----------|-------------|
| Publish  | `.github/workflows/publish.yml` | tag v*    | PyPI release|

### Conventions