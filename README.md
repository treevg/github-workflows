# github-workflows

A centralized repository hosting production-ready, reusable GitHub Actions workflows (`workflow_call`) for automated testing, SemVer releases, branch snapshot pre-releases, and deployment orchestration.

Consumer repositories reference these workflows directly with **~5 lines of YAML** instead of duplicating workflow logic across every project.

---

## The Reusable Workflows

| Workflow | File | Description | Triggers |
| :--- | :--- | :--- | :--- |
| **🧪 CI** | `.github/workflows/ci.yml` | Cross-platform test matrix (Ubuntu + macOS) and PR changelog linter. | `workflow_call`, `push`, `pull_request` |
| **🏷️ Release** | `.github/workflows/release.yml` | Git-tag SemVer bumping, changelog promotion, test/prep/deploy hooks, atomic commit/tag, and GitHub Release. | `workflow_call`, `workflow_dispatch` |
| **📸 Snapshot** | `.github/workflows/snapshot.yml` | Branch pre-release (e.g. `1.3.4-feature-name.1`), staging deploy hook, and GitHub Pre-Release. | `workflow_call`, `workflow_dispatch` |

---

## Consumer Repository Setup

In any consumer repository, simply add the caller workflows inside `.github/workflows/`:

### 1. `.github/workflows/ci.yml`
```yaml
name: 🧪 CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  ci:
    uses: treevg/github-workflows/.github/workflows/ci.yml@v1
```

### 2. `.github/workflows/release.yml`
```yaml
name: 🏷️ Release

on:
  workflow_dispatch:
    inputs:
      bump:
        description: 'SemVer Version Bump'
        required: true
        default: 'patch'
        type: choice
        options:
          - patch
          - minor
          - major
      dry_run:
        description: 'Dry run (preview release without committing, tagging, or pushing)'
        required: false
        default: false
        type: boolean

jobs:
  release:
    uses: treevg/github-workflows/.github/workflows/release.yml@v1
    with:
      bump: ${{ inputs.bump }}
      dry_run: ${{ inputs.dry_run }}
    secrets: inherit
```

### 3. `.github/workflows/snapshot.yml`
```yaml
name: 📸 Snapshot

on:
  workflow_dispatch:
    inputs:
      run_tests:
        description: 'Run automated test suite before pre-release'
        required: false
        default: true
        type: boolean
      dry_run:
        description: 'Dry run (preview snapshot version without committing, tagging, or pushing)'
        required: false
        default: false
        type: boolean

jobs:
  snapshot:
    uses: treevg/github-workflows/.github/workflows/snapshot.yml@v1
    with:
      run_tests: ${{ inputs.run_tests }}
      dry_run: ${{ inputs.dry_run }}
    secrets: inherit
```

---

## Project Customization Hooks (`.ci/actions/`)

The shared workflows automatically detect and execute project-specific hooks located in `.ci/actions/` within the consumer repository:

- **`.ci/actions/run-tests/action.yml`**: Custom test execution (pytest, npm test, cargo test, ./tests/run_tests.sh). If omitted, falls back to `tests/run_tests.sh` if present.
- **`.ci/actions/prepare-release/action.yml`**: On-the-fly codebase modifications (e.g. bumping package.json, Cargo.toml). Any tracked files modified here are automatically committed before release.
- **`.ci/actions/deploy/action.yml`**: Deployment execution for staging (`inputs.target == 'staging'`) and production (`inputs.target == 'production'`).
