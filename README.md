# FastAPI Microservice Template

Jumpstart your FastAPI projects. This starter template features an organized layout, Docker integration, Prettier, and
standard Git configs.

---

## Architecture Overview

The project is structured according to **Clean Architecture** patterns, ensuring a separation of concerns between
external deliveries (FastAPI), business orchestration (Services), and database interactions (Repositories).

```
HTTP Request ──> Delivery Layer (API) ──> Service Layer (Business) ──> Repository Layer ──> DB
```

For details, refer to the [Architecture & Database Guide](docs/architecture.md).

---

## Key Features

- **Async-First Execution**: Database queries are executed asynchronously using `SQLAlchemy` and `AsyncPG`.
- **Clean Code Architecture**: Strictly separated boundaries (API, Service, Repository, Model).
- **Zero Trust Authentication**: Integrates with the Ory Stack (Kratos, Oathkeeper, Keto). Validates JWTs forwarded by
  Oathkeeper acting as an Identity & Access Proxy.
- **Modern Development Tooling**: Configured Ruff linting, strict mypy type validations, and pre-commit hooks.
- **Testing & Coverage**: Standardized testing setup using `pytest` enforcing a 90% coverage gate.
- **Container Ready**: Dockerfile and docker-compose configurations included.

---

## Quick Start

### 1. Run the Database

```bash
docker compose up -d postgres
```

### 2. Setup Virtual Environment & Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Setup Configuration

```bash
cp .env.example .env
# Edit .env and generate SECRET_KEY:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 4. Run Migrations & Start Server

```bash
alembic upgrade head
uvicorn main:app --reload
```

---

## Documentation Index

Explore our manuals and guides to understand the project setup and conventions:

1. [Project Structure Guide](project-structure.md) — Module layout, layer responsibilities, extension workflows, and
   file map.
2. [Architecture & Database Guide](docs/architecture.md) — Clean Architecture layers, repository patterns, and Alembic
   workflows.
3. [Development Guide](docs/development.md) — Local setup instructions, environment variables reference, Docker Compose
   commands, and troubleshooting FAQ.
4. [API Guidelines & Endpoints](docs/api.md) — JWT auth structure, versioning, and endpoints reference.
5. [Testing Guide](docs/testing.md) — pytest-asyncio settings, mocking, unit/integration splits, and coverage rules.
6. [Pre-push Checks Guide](docs/pre-push-checks.md) — Step-by-step developer guidelines for running local format, lint,
   type-checking, test, and security gates.
