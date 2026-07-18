# Pre-push Checks Guide

This document outlines the standard quality gates, code formatting, static typing, test execution, and security checks
that developers should run locally before pushing code to the remote repository.

Adhering to these local checks ensures that the `main` branch remains stable, prevents build failures in the GitHub
Actions CI pipeline, and conserves GitHub Actions runner resources.

---

## Pre-push Checklist

Before running `git push`, make sure you have run and resolved all of the following checks locally:

| Step  | Area                           | Command                                   | Expected Result                                                |
| :---- | :----------------------------- | :---------------------------------------- | :------------------------------------------------------------- |
| **1** | Python Format & Import Sorting | `ruff format .` <br> `ruff check --fix .` | Formatted python files, removed unused imports, sorted imports |
| **2** | Config & Doc Formatting        | `npx prettier --write .`                  | Formatted Markdown, JSON, YAML according to `.prettierrc`      |
| **3** | Lint & Style Checks            | `ruff check .`                            | Zero style violations (`All checks passed!`)                   |
| **4** | Static Type Analysis           | `mypy .`                                  | No type errors (`Success: no issues found...`)                 |
| **5** | Run Tests & Coverage           | `pytest`                                  | All test cases PASSED and coverage meets requirements          |
| **6** | Dependency Audit               | `pip-audit -r requirements.txt`           | No packages with known vulnerabilities                         |
| **7** | Secret Scanning                | `detect-secrets scan`                     | No credentials or private tokens detected in git history       |

---

## Detailed Run Commands

### 1. Code Formatting & Import Sorting (Ruff & Prettier)

We enforce strict formatting rules across Python source files, configuration files (JSON/YAML), and documentation
(Markdown).

- **Step 1.1: Format Python Source & Sort Imports (Ruff)** We use **Ruff** – an extremely fast Rust-based Python linter
  and formatter. Run the following commands to format code, remove unused imports, and sort imports according to PEP 8
  standards:

    ```bash
    # Copes with indentation, layout, and syntax structure
    ruff format .

    # Automatically removes unused imports and sorts imports (isort-compatible rules)
    ruff check . --select I,F401 --fix
    ```

    _(Tip: Run `ruff check --fix .` to automatically resolve all autofixable lint and style errors)._

- **Step 1.2: Format Configurations & Documentation (Prettier)** We use **Prettier** to enforce formatting rules defined
  in [.prettierrc](../.prettierrc) for all non-Python files (such as `.json`, `.yml`, `.yaml`, `.md`):
    ```bash
    # Format all JSON, YAML, and Markdown files in the workspace
    npx prettier --write .
    ```

### 2. Linting & Style Rules (Ruff)

After formatting your code, check for remaining code quality violations (complexity, styling, naming conventions, etc.):

```bash
ruff check .
```

**Requirement:** Must print `All checks passed!` before pushing code.

### 3. Static Type Checking (mypy)

To prevent runtime type mismatch errors, the project configures strict mypy rules (`strict = true`).

Run static analysis against the workspace:

```bash
mypy .
```

**Requirement:** Must print `Success: no issues found in X source files`. Fix any type issues before pushing.

### 4. Testing & Coverage Gate (pytest)

Run the full test suite to verify that your changes do not introduce regressions:

```bash
pytest
```

- **Coverage Requirements:** The project enforces a **90%** coverage gate in `pyproject.toml` (using
  `--cov-fail-under=90`). When authoring new features, you must write corresponding test cases under `tests/unit/` to
  ensure coverage stays above this threshold.

### 5. Security & Vulnerability Scans

- **Dependency Auditing:** Audit installed packages against databases of known security issues:

    ```bash
    pip-audit -r requirements.txt
    ```

- **Secret Detection:** Scan the workspace to prevent accidental commits containing credentials, API keys, or security
  tokens:
    ```bash
    detect-secrets scan
    ```

---

## Automating with Pre-commit Hooks (Recommended)

To avoid running these commands manually before each commit, we use **pre-commit** to run formatting and linting
automatically.

### Configuration File

Ensure you have a `.pre-commit-config.yaml` file in the root of the repository with the following hooks configured:

```yaml
repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.15.22
      hooks:
          - id: ruff
            args: [--fix]
          - id: ruff-format

    - repo: https://github.com/pre-commit/mirrors-prettier
      rev: v4.0.0-alpha.8
      hooks:
          - id: prettier
            types_or: [markdown, json, yaml]

    - repo: https://github.com/Yelp/detect-secrets
      rev: v1.5.0
      hooks:
          - id: detect-secrets

    - repo: local
      hooks:
          - id: mypy
            name: mypy
            entry: mypy
            language: system
            types: [python]
            files: ^(app|tests)/
```

### Installation

Activate pre-commit hooks locally:

```bash
pre-commit install
```

Now, every time you run `git commit`, `ruff` and `mypy` will automatically check your modified files. The commit will be
rejected if any checks fail, helping you resolve errors immediately.
