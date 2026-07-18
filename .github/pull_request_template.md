<!--
Thank you for contributing! Please fill out this template before submitting your Pull Request.
-->

## Description

Please include a summary of the change, target problem, and motivation. List any external dependencies that are required
for this change.

Fixes # (issue number or discussion link)

## Type of Change

Please mark the options that are relevant:

- [ ] 🐛 **Bug Fix** (non-breaking change which fixes an issue)
- [ ] 🚀 **New Feature** (non-breaking change which adds functionality)
- [ ] ⚠️ **Breaking Change** (fix or feature that would cause existing functionality to break or behave differently)
- [ ] 📚 **Documentation Update** (changes to docs, comments, or README)
- [ ] 🛠️ **Refactoring / Maintenance** (code changes that neither fix a bug nor add a feature, code cleanup,
      dependencies)
- [ ] ⚙️ **CI/CD / Build System** (updates to GitHub Actions workflows, Dockerfiles, or dependencies management)

## How Has This Been Tested?

Please describe the tests that you ran to verify your changes.

- [ ] **Unit Tests**: Ran `pytest tests/unit/` to verify isolation logic and mocks.
- [ ] **Integration Tests**: Ran `pytest tests/integration/` to verify HTTP endpoints and DB repositories.
- [ ] **Code Coverage**: Confirmed that code coverage is at or above the **90%** gate.
- [ ] **Manual Verification**: (Please describe any manual verification steps, API client testing, or output
      verification)

## Checklist

Before submitting this PR, please check the following:

- [ ] My code conforms to the project's formatting and styling guidelines (lint and format checks with Ruff, Black, and
      isort pass).
- [ ] My changes do not introduce any new static type check warnings (`mypy app` passes without errors).
- [ ] I have executed security checks locally (`bandit`, `pip-audit`, `detect-secrets`) and fixed any issues.
- [ ] I have updated corresponding documentation or added inline code comments for complex sections.
- [ ] My changes generate no new database migration warnings (if database models were modified, Alembic migration files
      have been generated and tested).
- [ ] I have self-reviewed my own code.

## Screenshots / Evidence (if applicable)

_Add screenshots, logs, or command-line output showing the validation or changes._
