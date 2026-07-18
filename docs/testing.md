# Testing Guide

This document describes the testing setup, execution commands, and coverage rules.

---

## Testing Framework

The test suite runs on [pytest](https://docs.pytest.org/en/latest/) and
[pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio).

### Structure

- **Unit Tests (`tests/unit/`)**: Verify services, utilities, and helper functions in isolation using mocks (no database
  or external connections).
- **Integration Tests (`tests/integration/`)**: Verify full API request-response flows using a test client. They
  interact with an isolated database session that rolls back changes automatically after each test.

---

## Execution Commands

- **Run all tests**:
    ```bash
    pytest
    ```
- **Run with code coverage analysis**:
    ```bash
    pytest --cov=app --cov-report=term-missing
    ```
- **Run specific test paths**:
    ```bash
    pytest tests/unit/
    pytest tests/integration/
    ```

---

## Coverage Gate

The template enforces a strict test coverage limit of **90%** via `pyproject.toml` (`--cov-fail-under=90`). Pull request
checks in GitHub Actions will fail if test coverage drops below this threshold.

---

## Related Documentation

- [Development Guide](development.md)
- [Architecture Guide](architecture.md)
- [Pre-push Checks Guide](pre-push-checks.md)
